"""Acceptance tests for Kafka infrastructure."""

import asyncio
import json

import pytest
from aiokafka import AIOKafkaConsumer

from src.worker.config import worker_config
from src.worker.consumer import KafkaConsumer
from src.worker.handlers.test_handler import TestMessageHandler

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.acceptance,  # Mark as acceptance test
]


class TestKafkaInfrastructure:
    """Acceptance tests for Kafka infrastructure using real Kafka testcontainer."""

    async def test_consumer_connects_to_kafka(self, kafka_bootstrap_servers):
        """Test that consumer can connect to Kafka successfully."""
        # Create consumer with test Kafka instance
        test_consumer = AIOKafkaConsumer(
            worker_config.PROBLEM_GENERATION_TOPIC,
            bootstrap_servers=kafka_bootstrap_servers,
            group_id="test-consumer-group",
            auto_offset_reset="earliest",
        )

        await test_consumer.start()

        try:
            # Verify connection by checking subscriptions
            subscription = test_consumer.subscription()
            assert subscription is not None
            assert worker_config.PROBLEM_GENERATION_TOPIC in subscription
        finally:
            await test_consumer.stop()

    async def test_consumer_processes_message(
        self, kafka_bootstrap_servers, kafka_producer, test_message
    ):
        """Test that consumer receives and processes messages from Kafka."""
        # Track if handler was called
        messages_received = []

        # Custom handler that captures messages
        class CaptureHandler:
            async def handle(self, message):
                messages_received.append(message)

        # Create consumer
        consumer = KafkaConsumer()
        consumer.handler = CaptureHandler()

        # Temporarily override bootstrap servers for test
        original_servers = worker_config.KAFKA_BOOTSTRAP_SERVERS
        worker_config.KAFKA_BOOTSTRAP_SERVERS = kafka_bootstrap_servers

        try:
            # Start consumer in background
            consumer_task = asyncio.create_task(consumer.run())

            # Wait for consumer to connect
            await asyncio.sleep(2)

            # Publish test message
            await kafka_producer.send(
                worker_config.PROBLEM_GENERATION_TOPIC, value=test_message
            )
            await kafka_producer.flush()

            # Wait for message to be processed
            await asyncio.sleep(2)

            # Verify message was received and processed
            assert len(messages_received) == 1
            assert messages_received[0] == test_message

        finally:
            # Cleanup
            worker_config.KAFKA_BOOTSTRAP_SERVERS = original_servers
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

    async def test_consumer_commits_offset_after_success(
        self, kafka_bootstrap_servers, kafka_producer
    ):
        """Test that consumer commits offset after successfully processing a message."""
        # Create consumer with unique group ID to avoid offset conflicts
        test_group = "offset-commit-test-group"
        test_topic = worker_config.PROBLEM_GENERATION_TOPIC

        # First, publish our test message
        message = {"test": "offset_commit", "value": 42}
        await kafka_producer.send(test_topic, value=message)
        await kafka_producer.flush()

        # Create consumer starting from latest (skip old messages)
        consumer = AIOKafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            group_id=test_group,
            auto_offset_reset="latest",  # Start from end, only read our message
            enable_auto_commit=False,  # Manual commits like production
        )

        await consumer.start()

        # Wait for initial assignment
        await asyncio.sleep(1)

        # Now send another message that consumer will receive
        await kafka_producer.send(test_topic, value=message)
        await kafka_producer.flush()

        try:
            # Consume and commit
            message_count = 0
            async for msg in consumer:
                # Deserialize message (it's bytes)
                import json

                received = json.loads(msg.value.decode("utf-8"))
                assert received == message

                # Commit offset
                await consumer.commit()

                message_count += 1
                # Only process our one message
                if message_count >= 1:
                    break

            # Verify offset was committed
            partitions = consumer.assignment()
            for partition in partitions:
                committed = await consumer.committed(partition)
                assert committed is not None
                assert committed > 0

        finally:
            await consumer.stop()

    async def test_consumer_handles_invalid_json(self, kafka_bootstrap_servers):
        """Test that consumer handles invalid JSON gracefully without crashing."""
        from aiokafka import AIOKafkaProducer

        # Create consumer
        consumer = KafkaConsumer()

        # Track errors

        class ErrorCaptureHandler:
            async def handle(self, message):
                # This shouldn't be called for invalid JSON
                pass

        consumer.handler = ErrorCaptureHandler()

        # Override bootstrap servers
        original_servers = worker_config.KAFKA_BOOTSTRAP_SERVERS
        worker_config.KAFKA_BOOTSTRAP_SERVERS = kafka_bootstrap_servers

        # Create raw producer (no JSON serializer)
        producer = AIOKafkaProducer(bootstrap_servers=kafka_bootstrap_servers)
        await producer.start()

        try:
            # Start consumer
            consumer_task = asyncio.create_task(consumer.run())
            await asyncio.sleep(2)

            # Send invalid JSON
            await producer.send(
                worker_config.PROBLEM_GENERATION_TOPIC,
                value=b"this is not valid json {{",
            )
            await producer.flush()

            # Wait a bit
            await asyncio.sleep(2)

            # Consumer should still be running (not crashed)
            assert (
                not consumer_task.done()
            ), "Consumer should handle invalid JSON without crashing"

        finally:
            # Cleanup
            worker_config.KAFKA_BOOTSTRAP_SERVERS = original_servers
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
            await producer.stop()
