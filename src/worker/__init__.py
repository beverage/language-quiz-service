"""Background worker for async problem generation."""

import asyncio
import logging

from src.worker.consumer import KafkaConsumer

logger = logging.getLogger(__name__)

_worker_task: asyncio.Task | None = None


async def start_worker() -> None:
    """
    Start the background worker task.

    This starts a Kafka consumer that processes problem generation requests
    in the background, running alongside the FastAPI application.
    """
    global _worker_task

    if _worker_task is not None:
        logger.warning("Worker task already running")
        return

    logger.info("Starting background worker...")
    consumer = KafkaConsumer()
    _worker_task = asyncio.create_task(consumer.run())
    logger.info("Background worker started successfully")


async def stop_worker() -> None:
    """
    Stop the background worker task gracefully.

    Waits for current message processing to complete before shutting down.
    """
    global _worker_task

    if _worker_task is None:
        logger.warning("Worker task not running")
        return

    logger.info("Stopping background worker...")
    _worker_task.cancel()

    try:
        await _worker_task
    except asyncio.CancelledError:
        logger.info("Background worker stopped successfully")

    _worker_task = None


__all__ = ["start_worker", "stop_worker"]
