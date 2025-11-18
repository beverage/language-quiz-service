"""Tests for queue service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.problems import GrammarProblemConstraints
from src.services.queue_service import QueueService

pytestmark = pytest.mark.asyncio


class TestQueueService:
    """Test queue service message publishing."""

    async def test_publish_single_request(self):
        """Test publishing a single problem generation request."""
        service = QueueService()

        # Mock the Kafka producer
        mock_producer = AsyncMock()
        service.producer = mock_producer

        constraints = GrammarProblemConstraints()
        enqueued_count, request_id = await service.publish_problem_generation_request(
            constraints=constraints,
            statement_count=4,
            topic_tags=["test_data"],
            count=1,
        )

        assert enqueued_count == 1
        assert isinstance(request_id, str)
        assert mock_producer.send.call_count == 1
        assert mock_producer.flush.call_count == 1

    async def test_publish_multiple_requests(self):
        """Test publishing multiple problem generation requests."""
        service = QueueService()

        # Mock the Kafka producer
        mock_producer = AsyncMock()
        service.producer = mock_producer

        enqueued_count, request_id = await service.publish_problem_generation_request(
            constraints=None,
            statement_count=4,
            topic_tags=["test_data"],
            count=10,
        )

        assert enqueued_count == 10
        # New behavior: single request_id for all messages in a batch
        assert isinstance(request_id, str)
        # 10 messages should be sent, all with the same generation_request_id
        assert mock_producer.send.call_count == 10
        assert mock_producer.flush.call_count == 1

    async def test_publish_with_trace_context(self):
        """Test that trace context is injected into message headers."""
        service = QueueService()

        # Mock the Kafka producer
        mock_producer = AsyncMock()
        service.producer = mock_producer

        # Mock trace context injection
        with patch("src.services.queue_service.inject_trace_context") as mock_inject:
            mock_inject.return_value = {"traceparent": "test-trace-id"}

            await service.publish_problem_generation_request(
                count=1,
                topic_tags=["test_data"],
            )

            # Verify trace context was injected
            mock_inject.assert_called_once()

            # Verify headers were passed to send()
            call_args = mock_producer.send.call_args
            assert call_args is not None
            headers = call_args.kwargs.get("headers")
            assert headers is not None
            assert len(headers) > 0

    async def test_publish_continues_on_partial_failure(self):
        """Test that partial send failures don't stop remaining messages."""
        service = QueueService()

        # Mock the Kafka producer to fail on 2nd message
        mock_producer = AsyncMock()
        mock_producer.send.side_effect = [
            AsyncMock(),  # Success
            Exception("Kafka error"),  # Failure
            AsyncMock(),  # Success
        ]
        service.producer = mock_producer

        enqueued_count, request_id = await service.publish_problem_generation_request(
            count=3,
            topic_tags=["test_data"],
        )

        # Should return 2 (2 successful out of 3)
        assert enqueued_count == 2
        # New behavior: single request_id regardless of partial failure
        assert isinstance(request_id, str)
        assert mock_producer.send.call_count == 3

    async def test_close_producer(self):
        """Test closing the Kafka producer."""
        service = QueueService()

        # Mock producer
        mock_producer = AsyncMock()
        service.producer = mock_producer

        await service.close()

        # Verify producer was stopped
        mock_producer.stop.assert_called_once()
        assert service.producer is None

    async def test_close_when_no_producer(self):
        """Test closing when producer doesn't exist."""
        service = QueueService()

        # Should not raise
        await service.close()

        assert service.producer is None
