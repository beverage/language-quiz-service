"""Kafka consumer for processing problem generation requests."""

import asyncio
import json
import logging
import time
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from src.worker import metrics
from src.worker.config import worker_config
from src.worker.handlers.problem_handler import ProblemGenerationHandler

logger = logging.getLogger(__name__)


class KafkaConsumer:  # pragma: no cover
    """
    Asynchronous Kafka consumer for problem generation requests.

    This consumer runs in the background, polling for messages from the
    problem generation topic and dispatching them to appropriate handlers.
    """

    def __init__(self):
        """Initialize the Kafka consumer."""
        self.consumer: AIOKafkaConsumer | None = None
        self.running = False
        self.handler = ProblemGenerationHandler()

    async def run(self) -> None:
        """
        Main consumer loop.

        Continuously polls for messages and processes them until cancelled.
        Handles reconnection on errors.
        """
        self.running = True

        while self.running:
            try:
                await self._consume_messages()
            except asyncio.CancelledError:
                logger.info("Consumer cancelled, shutting down...")
                break
            except KafkaError as e:
                logger.error(f"Kafka error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"Unexpected error in consumer: {e}", exc_info=True)
                await asyncio.sleep(5)
            finally:
                await self._cleanup()

    async def _consume_messages(self) -> None:
        """
        Connect to Kafka and process messages.

        Creates consumer, subscribes to topic, and processes messages
        until an error occurs or the consumer is cancelled.
        """
        # Create consumer
        self.consumer = AIOKafkaConsumer(
            worker_config.PROBLEM_GENERATION_TOPIC,
            bootstrap_servers=worker_config.KAFKA_BOOTSTRAP_SERVERS,
            group_id=worker_config.CONSUMER_GROUP_ID,
            auto_offset_reset=worker_config.CONSUMER_AUTO_OFFSET_RESET,
            enable_auto_commit=False,  # Manual commit for reliability
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            max_poll_interval_ms=worker_config.MAX_POLL_INTERVAL_MS,
            session_timeout_ms=worker_config.SESSION_TIMEOUT_MS,
        )

        # Start consumer
        await self.consumer.start()
        logger.info(
            f"Connected to Kafka at {worker_config.KAFKA_BOOTSTRAP_SERVERS}, "
            f"subscribed to topic: {worker_config.PROBLEM_GENERATION_TOPIC}"
        )

        try:
            # Process messages
            async for message in self.consumer:
                await self._process_message(message)
        finally:
            await self.consumer.stop()

    async def _process_message(self, message: Any) -> None:
        """
        Process a single Kafka message.

        Args:
            message: Kafka message containing problem generation request
        """
        start_time = time.time()
        metrics.increment_active_tasks()

        try:
            logger.info(
                f"Processing message from partition {message.partition}, "
                f"offset {message.offset}"
            )

            # Delegate to handler with message headers for trace context
            await self.handler.handle(message.value, headers=message.headers)

            # Commit offset after successful processing
            if self.consumer:
                await self.consumer.commit()

            # Record success metrics
            duration = time.time() - start_time
            metrics.record_processing_duration(
                duration, topic=worker_config.PROBLEM_GENERATION_TOPIC
            )
            metrics.increment_messages_processed(
                topic=worker_config.PROBLEM_GENERATION_TOPIC
            )

            logger.info(
                f"Successfully processed message at offset {message.offset} "
                f"in {duration:.2f}s"
            )

        except Exception as e:
            logger.error(
                f"Error processing message at offset {message.offset}: {e}",
                exc_info=True,
            )

            # Record failure metrics
            metrics.increment_messages_failed(
                topic=worker_config.PROBLEM_GENERATION_TOPIC,
                error_type=type(e).__name__,
            )

            # Don't commit - message will be reprocessed
            # In production, might want to send to DLQ after N retries
        finally:
            metrics.decrement_active_tasks()

    async def _cleanup(self) -> None:
        """Clean up consumer resources."""
        if self.consumer:
            try:
                await self.consumer.stop()
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")
            finally:
                self.consumer = None
