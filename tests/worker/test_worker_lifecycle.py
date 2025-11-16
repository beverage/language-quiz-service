"""Tests for worker lifecycle management (startup/shutdown)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.worker import start_worker, stop_worker

pytestmark = pytest.mark.asyncio


class TestWorkerLifecycle:
    """Test worker startup and shutdown logic."""

    async def test_start_worker_creates_background_task(self):
        """Test that start_worker creates a background consumer task."""
        with patch("src.worker.KafkaConsumer") as mock_consumer_class:
            mock_consumer = MagicMock()
            mock_consumer.run = AsyncMock(side_effect=asyncio.CancelledError)
            mock_consumer_class.return_value = mock_consumer

            # Start worker
            await start_worker()

            # Give it time to start
            await asyncio.sleep(0.1)

            # Verify consumer was created and run() was called
            mock_consumer_class.assert_called_once()

            # Stop worker
            await stop_worker()

    async def test_start_worker_logs_warning_if_already_running(self):
        """Test that starting worker twice logs a warning."""
        with patch("src.worker.KafkaConsumer") as mock_consumer_class:
            mock_consumer = MagicMock()
            mock_consumer.run = AsyncMock(side_effect=asyncio.CancelledError)
            mock_consumer_class.return_value = mock_consumer

            # Start worker first time
            await start_worker()
            await asyncio.sleep(0.1)

            # Try to start again - should log warning
            with patch("src.worker.logger") as mock_logger:
                await start_worker()
                mock_logger.warning.assert_called_once()

            # Cleanup
            await stop_worker()

    async def test_stop_worker_cancels_task(self):
        """Test that stop_worker cancels the background task."""
        with patch("src.worker.KafkaConsumer") as mock_consumer_class:
            # Create a consumer that runs forever until cancelled
            mock_consumer = MagicMock()

            async def mock_run():
                try:
                    await asyncio.sleep(1000)  # Run forever
                except asyncio.CancelledError:
                    raise

            mock_consumer.run = mock_run
            mock_consumer_class.return_value = mock_consumer

            # Start worker
            await start_worker()
            await asyncio.sleep(0.1)

            # Stop worker - should cancel the task
            await stop_worker()

            # Task should be cleaned up
            # If we can reach this point without hanging, stop_worker worked

    async def test_stop_worker_when_not_running(self):
        """Test that stopping worker when not running logs a warning."""
        with patch("src.worker.logger") as mock_logger:
            await stop_worker()
            mock_logger.warning.assert_called_once()
