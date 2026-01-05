"""Observability metrics for worker operations."""

import logging
import os

logger = logging.getLogger(__name__)

# Import OpenTelemetry only if enabled
OTEL_ENABLED = bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))

if OTEL_ENABLED:  # pragma: no cover
    from opentelemetry import metrics
    from opentelemetry.metrics import Counter, Histogram, ObservableGauge

    # Get meter
    meter = metrics.get_meter("worker")

    # Message processing metrics
    messages_processed_counter: Counter = meter.create_counter(
        name="worker.messages.processed",
        description="Total number of messages processed by worker",
        unit="1",
    )

    messages_failed_counter: Counter = meter.create_counter(
        name="worker.messages.failed",
        description="Total number of messages that failed processing",
        unit="1",
    )

    messages_malformed_counter: Counter = meter.create_counter(
        name="worker.messages.malformed",
        description="Total number of malformed messages (missing required fields)",
        unit="1",
    )

    processing_duration_histogram: Histogram = meter.create_histogram(
        name="worker.message.processing_duration",
        description="Time taken to process a single message",
        unit="s",
    )

    # Queue metrics (will be updated periodically)
    _queue_length: int = 0

    def _get_queue_length(options):
        """Callback for queue length gauge."""
        from opentelemetry.metrics import Observation

        yield Observation(_queue_length)

    queue_length_gauge: ObservableGauge = meter.create_observable_gauge(
        name="worker.queue.length",
        callbacks=[_get_queue_length],
        description="Current number of messages in the queue",
        unit="1",
    )

    # Worker status
    _active_tasks: int = 0

    def _get_active_tasks(options):
        """Callback for active tasks gauge."""
        from opentelemetry.metrics import Observation

        yield Observation(_active_tasks)

    active_tasks_gauge: ObservableGauge = meter.create_observable_gauge(
        name="worker.tasks.active",
        callbacks=[_get_active_tasks],
        description="Number of currently active worker tasks",
        unit="1",
    )

    logger.info("✅ Worker metrics initialized with OpenTelemetry")

else:  # pragma: no cover
    # Dummy implementations when OpenTelemetry is disabled
    logger.info("⚡ Worker metrics disabled (no OTEL_EXPORTER_OTLP_ENDPOINT set)")

    class DummyCounter:  # pragma: no cover
        def add(self, *args, **kwargs):  # pragma: no cover
            pass  # pragma: no cover

    class DummyHistogram:  # pragma: no cover
        def record(self, *args, **kwargs):  # pragma: no cover
            pass  # pragma: no cover

    messages_processed_counter = DummyCounter()
    messages_failed_counter = DummyCounter()
    messages_malformed_counter = DummyCounter()
    processing_duration_histogram = DummyHistogram()

    _queue_length = 0
    _active_tasks = 0


# Public API for updating metrics
def increment_messages_processed(topic: str = "unknown") -> None:  # pragma: no cover
    """Increment the count of successfully processed messages."""
    messages_processed_counter.add(1, {"topic": topic})


def increment_messages_failed(
    topic: str = "unknown", error_type: str = "unknown"
) -> None:  # pragma: no cover
    """Increment the count of failed messages."""
    messages_failed_counter.add(1, {"topic": topic, "error_type": error_type})


def increment_messages_malformed(
    topic: str = "unknown", reason: str = "unknown"
) -> None:  # pragma: no cover
    """Increment the count of malformed messages."""
    messages_malformed_counter.add(1, {"topic": topic, "reason": reason})


def record_processing_duration(
    duration_seconds: float, topic: str = "unknown"
) -> None:  # pragma: no cover
    """Record the time taken to process a message."""
    processing_duration_histogram.record(duration_seconds, {"topic": topic})


def set_queue_length(length: int) -> None:  # pragma: no cover
    """Update the current queue length metric."""
    global _queue_length
    _queue_length = length


def increment_active_tasks() -> None:  # pragma: no cover
    """Increment the active tasks counter."""
    global _active_tasks
    _active_tasks += 1


def decrement_active_tasks() -> None:  # pragma: no cover
    """Decrement the active tasks counter."""
    global _active_tasks
    _active_tasks = max(0, _active_tasks - 1)


__all__ = [
    "increment_messages_processed",
    "increment_messages_failed",
    "increment_messages_malformed",
    "record_processing_duration",
    "set_queue_length",
    "increment_active_tasks",
    "decrement_active_tasks",
]
