"""Tests for worker metrics."""

import pytest

from src.worker import metrics


class TestWorkerMetrics:
    """Test worker metrics recording functions."""

    def test_increment_messages_processed(self):
        """Test incrementing messages processed counter."""
        # Should not raise error
        metrics.increment_messages_processed(topic="test-topic")
        metrics.increment_messages_processed()  # Default topic

    def test_increment_messages_failed(self):
        """Test incrementing messages failed counter."""
        # Should not raise error
        metrics.increment_messages_failed(topic="test-topic", error_type="ValueError")
        metrics.increment_messages_failed()  # Defaults

    def test_record_processing_duration(self):
        """Test recording processing duration."""
        # Should not raise error
        metrics.record_processing_duration(1.5, topic="test-topic")
        metrics.record_processing_duration(0.1)  # Default topic

    def test_set_queue_length(self):
        """Test setting queue length gauge."""
        metrics.set_queue_length(0)
        metrics.set_queue_length(100)
        metrics.set_queue_length(5)

    def test_active_tasks_increment_decrement(self):
        """Test incrementing and decrementing active tasks."""
        # Get initial state
        initial = metrics._active_tasks

        # Increment
        metrics.increment_active_tasks()
        assert metrics._active_tasks == initial + 1

        # Decrement
        metrics.decrement_active_tasks()
        assert metrics._active_tasks == initial

        # Decrement below zero should clamp to 0
        metrics.decrement_active_tasks()
        metrics.decrement_active_tasks()
        assert metrics._active_tasks == 0


class TestHandlerLogic:
    """Test TestMessageHandler logic."""

    @pytest.mark.asyncio
    async def test_handler_processes_message(self):
        """Test that TestMessageHandler processes messages."""
        from src.worker.handlers.test_handler import TestMessageHandler

        handler = TestMessageHandler()

        # Should not raise error
        await handler.handle({"test": "data", "value": 123})
        await handler.handle({})  # Empty message
        await handler.handle({"complex": {"nested": "data"}})  # Nested
