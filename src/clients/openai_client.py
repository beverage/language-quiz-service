"""OpenAI client with observability and metadata capture.

Handles both reasoning models (gpt-5) and standard models (gpt-4o-mini),
returning LLMResponse with full metadata including reasoning traces when available.
"""

import logging
import time
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from opentelemetry import metrics, trace

from src.core.config import settings
from src.schemas.llm_response import LLMResponse

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry meter for custom LLM metrics
meter = metrics.get_meter(__name__)

llm_request_duration = meter.create_histogram(
    name="llm.request.duration",
    unit="ms",
    description="Duration of LLM API requests",
)

llm_request_total = meter.create_counter(
    name="llm.request.total",
    unit="1",
    description="Total number of LLM API requests",
)

llm_errors_total = meter.create_counter(
    name="llm.errors.total",
    unit="1",
    description="Total number of LLM API errors by type",
)

llm_tokens_input = meter.create_counter(
    name="llm.tokens.input",
    unit="1",
    description="Total input tokens consumed",
)

llm_tokens_output = meter.create_counter(
    name="llm.tokens.output",
    unit="1",
    description="Total output tokens generated",
)

llm_tokens_total = meter.create_counter(
    name="llm.tokens.total",
    unit="1",
    description="Total tokens (input + output)",
)

llm_tokens_reasoning = meter.create_counter(
    name="llm.tokens.reasoning",
    unit="1",
    description="Total reasoning tokens consumed (gpt-5 models)",
)


class OpenAIClient:
    """Async client for OpenAI with timeout, retry protection, and full observability."""

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            timeout=120.0,
            max_retries=1,
        )

    async def handle_request(
        self,
        prompt: str,
        model: str,
        operation: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request to OpenAI.

        Args:
            prompt: The prompt to send to OpenAI
            model: The model to use (e.g., "gpt-4o-mini", "gpt-5-nano-2025-08-07")
            operation: Optional operation name for metrics
            response_format: Optional JSON schema for structured output

        Returns:
            LLMResponse with content and metadata (reasoning data included for gpt-5)
        """
        start_time = time.time()
        status = "success"
        is_reasoning_model = "gpt-5" in model.lower()
        span = trace.get_current_span()

        try:
            # Build request parameters
            request_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "service_tier": "priority",
            }

            # Add reasoning effort for gpt-5 models
            if is_reasoning_model:
                request_params["reasoning_effort"] = "medium"

            if response_format:
                request_params["response_format"] = response_format

            response = await self.client.chat.completions.create(**request_params)
            duration_ms = (time.time() - start_time) * 1000

            # Extract usage information
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            # Extract reasoning data for gpt-5 models
            reasoning_tokens = None
            reasoning_content = None
            if is_reasoning_model:
                reasoning_tokens, reasoning_content = self._extract_reasoning_data(
                    response, usage
                )

            # Record metrics
            attributes = {"model": model, "status": status}
            if operation:
                attributes["operation"] = operation

            llm_request_duration.record(duration_ms, attributes=attributes)
            llm_request_total.add(1, attributes=attributes)

            if usage:
                llm_tokens_input.add(prompt_tokens, attributes=attributes)
                llm_tokens_output.add(completion_tokens, attributes=attributes)
                llm_tokens_total.add(total_tokens, attributes=attributes)

            if reasoning_tokens:
                llm_tokens_reasoning.add(reasoning_tokens, attributes=attributes)

            # Record span attributes
            if span.is_recording():
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.request.duration_ms", duration_ms)
                span.set_attribute("llm.response.id", response.id)
                span.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.usage.completion_tokens", completion_tokens)
                span.set_attribute("llm.usage.total_tokens", total_tokens)
                if operation:
                    span.set_attribute("llm.operation", operation)
                if reasoning_tokens is not None:
                    span.set_attribute("llm.usage.reasoning_tokens", reasoning_tokens)

            # Log completion
            reasoning_log = (
                f", reasoning={reasoning_tokens}" if reasoning_tokens else ""
            )
            logger.info(
                f"LLM request completed: operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"tokens=(prompt={prompt_tokens}, completion={completion_tokens}, "
                f"total={total_tokens}{reasoning_log})"
            )

            raw_content = response.choices[0].message.content
            return LLMResponse(
                content=self._clean_response(raw_content),
                model=model,
                response_id=response.id,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                reasoning_tokens=reasoning_tokens,
                reasoning_content=reasoning_content,
                raw_content=raw_content,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_type = self._categorize_error(e)

            error_attributes = {
                "model": model,
                "status": "error",
                "error_type": error_type,
            }
            if operation:
                error_attributes["operation"] = operation

            llm_request_duration.record(duration_ms, attributes=error_attributes)
            llm_request_total.add(1, attributes=error_attributes)
            llm_errors_total.add(1, attributes=error_attributes)

            if span.is_recording():
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.request.duration_ms", duration_ms)
                span.set_attribute("llm.error.type", error_type)
                span.set_attribute("llm.error.message", str(e))
                if operation:
                    span.set_attribute("llm.operation", operation)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            logger.error(
                f"LLM request failed: operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"error_type={error_type}, error={type(e).__name__}: {str(e)}"
            )
            raise

    def _extract_reasoning_data(self, response, usage) -> tuple[int | None, str | None]:
        """Extract reasoning tokens and content from gpt-5 response."""
        reasoning_tokens = None
        reasoning_content = None

        # Get reasoning tokens from usage details
        if usage and hasattr(usage, "completion_tokens_details"):
            details = usage.completion_tokens_details
            if details and hasattr(details, "reasoning_tokens"):
                reasoning_tokens = details.reasoning_tokens

        # Get reasoning content from message
        message = response.choices[0].message
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            reasoning_content = message.reasoning_content
        elif hasattr(message, "reasoning") and message.reasoning:
            if isinstance(message.reasoning, list):
                reasoning_content = "\n".join(str(step) for step in message.reasoning)
            else:
                reasoning_content = str(message.reasoning)

        return reasoning_tokens, reasoning_content

    def _categorize_error(self, error: Exception) -> str:
        """Categorize OpenAI errors into monitoring-friendly types."""
        error_message = str(error).lower()

        if "insufficient" in error_message and "quota" in error_message:
            return "insufficient_funds"
        if "quota" in error_message and "exceeded" in error_message:
            return "insufficient_funds"
        if isinstance(error, APITimeoutError):
            return "timeout"
        if "timeout" in error_message:
            return "timeout"
        if isinstance(error, RateLimitError):
            return "rate_limit"
        if "rate limit" in error_message or "rate_limit" in error_message:
            return "rate_limit"
        if isinstance(error, APIError):
            return "api_error"
        return "unknown"

    def _clean_response(self, raw_content: str | None) -> str:
        """Clean LLM response by removing markdown code blocks."""
        if raw_content is None:
            return ""
        if not raw_content:
            return raw_content

        cleaned = raw_content.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return cleaned.strip()
