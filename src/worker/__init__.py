"""Background worker for async problem generation."""

import asyncio
import logging

from src.worker.config import worker_config
from src.worker.consumer import KafkaConsumer

logger = logging.getLogger(__name__)

_worker_tasks: list[asyncio.Task] = []


async def start_worker() -> None:
    """
    Start the background worker tasks.

    This starts N Kafka consumers (based on WORKER_COUNT) that process
    problem generation requests in the background, running alongside
    the FastAPI application.

    All consumers join the same consumer group, and Kafka automatically
    distributes partition assignments among them.
    """
    global _worker_tasks

    if _worker_tasks:
        logger.warning("Worker tasks already running")
        return

    worker_count = worker_config.WORKER_COUNT
    logger.info(f"Starting {worker_count} background worker(s)...")

    # Create and start N consumer tasks
    for i in range(worker_count):
        consumer = KafkaConsumer()
        task = asyncio.create_task(consumer.run(), name=f"kafka-worker-{i+1}")
        _worker_tasks.append(task)
        logger.info(f"Worker {i+1}/{worker_count} started")

    logger.info(f"All {worker_count} background worker(s) started successfully")


async def stop_worker() -> None:
    """
    Stop all background worker tasks gracefully.

    Cancels all worker tasks and waits for current message processing
    to complete before shutting down.
    """
    global _worker_tasks

    if not _worker_tasks:
        logger.warning("No worker tasks running")
        return

    worker_count = len(_worker_tasks)
    logger.info(f"Stopping {worker_count} background worker(s)...")

    # Cancel all tasks
    for task in _worker_tasks:
        task.cancel()

    # Wait for all tasks to complete
    results = await asyncio.gather(*_worker_tasks, return_exceptions=True)

    # Log results
    cancelled_count = sum(1 for r in results if isinstance(r, asyncio.CancelledError))
    logger.info(
        f"Background workers stopped successfully ({cancelled_count}/{worker_count} cancelled)"
    )

    _worker_tasks = []


__all__ = ["start_worker", "stop_worker"]
