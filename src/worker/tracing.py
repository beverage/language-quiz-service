"""Distributed tracing utilities for worker operations."""  # pragma: no cover

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Check if OpenTelemetry is enabled
OTEL_ENABLED = bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))

if OTEL_ENABLED:  # pragma: no cover
    from opentelemetry import trace
    from opentelemetry.propagate import extract, inject
    from opentelemetry.trace import SpanKind


def inject_trace_context() -> dict[str, str]:  # pragma: no cover
    """
    Inject current OpenTelemetry trace context into a dict for Kafka headers.

    Returns:
        Dictionary with W3C trace context headers (traceparent, tracestate)
    """
    if not OTEL_ENABLED:
        return {}

    # Create a carrier dict for context injection
    carrier = {}
    inject(carrier)
    return carrier


def extract_trace_context(headers: list[tuple[str, bytes]] | None):  # pragma: no cover
    """
    Extract OpenTelemetry trace context from Kafka message headers.

    Args:
        headers: List of (key, value) tuples from Kafka message

    Returns:
        OpenTelemetry Context object, or None if no context or OTEL disabled
    """
    if not OTEL_ENABLED or not headers:
        return None

    # Convert Kafka headers to dict format for extraction
    carrier = {}
    for key, value in headers:
        # Decode bytes to string
        carrier[key] = value.decode("utf-8") if isinstance(value, bytes) else value

    # Extract context from carrier
    context = extract(carrier)
    return context


def create_worker_span(
    name: str,
    parent_context=None,
    attributes: dict[str, Any] | None = None,
):  # pragma: no cover
    """
    Create a worker span with proper parent context.

    Args:
        name: Span name (e.g., "worker.process_message")
        parent_context: Parent context extracted from Kafka message
        attributes: Additional span attributes

    Returns:
        Span object if OTEL enabled, else None
    """
    if not OTEL_ENABLED:
        return None

    tracer = trace.get_tracer(__name__)

    # Create span with parent context if provided
    if parent_context:
        # Use context as parent
        span = tracer.start_span(
            name,
            context=parent_context,
            kind=SpanKind.CONSUMER,  # This is a message consumer
        )
    else:
        # Create new trace
        span = tracer.start_span(name, kind=SpanKind.CONSUMER)

    # Add custom attributes
    if attributes and span:
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span


__all__ = [
    "inject_trace_context",
    "extract_trace_context",
    "create_worker_span",
]
