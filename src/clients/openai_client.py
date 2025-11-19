import logging
import time
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from opentelemetry import metrics, trace

from src.core.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry meter for custom LLM metrics
meter = metrics.get_meter(__name__)

# LLM request duration histogram
llm_request_duration = meter.create_histogram(
    name="llm.request.duration",
    unit="ms",
    description="Duration of LLM API requests",
)

# LLM request counter
llm_request_total = meter.create_counter(
    name="llm.request.total",
    unit="1",
    description="Total number of LLM API requests",
)

# LLM error counter (by error type)
llm_errors_total = meter.create_counter(
    name="llm.errors.total",
    unit="1",
    description="Total number of LLM API errors by type",
)

# Token usage counters
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


class OpenAIClient:
    """Async client for OpenAI with timeout and retry protection."""

    def __init__(self, api_key: str = None):
        # Configure timeouts to prevent hung requests
        # OpenAI Timeout expects: timeout, connect (optional)
        # If we pass just a float, it's the total timeout
        # For more control, use httpx.Timeout which OpenAI accepts
        self.client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            timeout=120.0,  # Total timeout for entire request (seconds)
            max_retries=5,  # Background workers can tolerate higher latency for reliability
        )

    async def handle_request(
        self,
        prompt: str,
        model: str,
        operation: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """
        Send a chat completion request to OpenAI and return the content string.

        Args:
            prompt: The prompt to send to OpenAI
            model: The model to use (e.g., "gpt-4o-mini", "gpt-5-nano-2025-08-07")
            operation: Optional operation name for metrics (e.g., "problem_generation", "sentence_validation")
            response_format: Optional JSON schema for structured output

        Returns:
            Cleaned response content
        """
        start_time = time.time()
        status = "success"

        # Determine if this is a reasoning model (o1, o3, or gpt-5 series)
        is_reasoning_model = any(x in model.lower() for x in ["o1", "o3", "gpt-5"])

        # Get current span for adding attributes
        span = trace.get_current_span()

        try:
            # Build request parameters
            request_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "service_tier": "priority",
            }

            # Only add reasoning_effort for reasoning models
            if is_reasoning_model:
                request_params["reasoning_effort"] = "minimal"

            # Add response format if provided
            if response_format:
                request_params["response_format"] = response_format

            response = await self.client.chat.completions.create(**request_params)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Extract usage information
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            # Prepare metric attributes
            attributes = {
                "model": model,
                "status": status,
            }
            if operation:
                attributes["operation"] = operation

            # Record metrics
            llm_request_duration.record(duration_ms, attributes=attributes)
            llm_request_total.add(1, attributes=attributes)

            # Record token usage
            if usage:
                token_attributes = attributes.copy()
                llm_tokens_input.add(prompt_tokens, attributes=token_attributes)
                llm_tokens_output.add(completion_tokens, attributes=token_attributes)
                llm_tokens_total.add(total_tokens, attributes=token_attributes)

            # Add span attributes for distributed tracing (following OpenTelemetry semantic conventions)
            if span.is_recording():
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.request.duration_ms", duration_ms)
                span.set_attribute("llm.response.id", response.id)

                # Token breakdown
                span.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.usage.completion_tokens", completion_tokens)
                span.set_attribute("llm.usage.total_tokens", total_tokens)

                if operation:
                    span.set_attribute("llm.operation", operation)

            # Log token usage for debugging and analysis
            logger.info(
                f"LLM request completed: operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"tokens=(prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens})"
            )

            raw_content = response.choices[0].message.content
            return self._clean_response(raw_content)

        except Exception as e:
            # Record error metrics
            duration_ms = (time.time() - start_time) * 1000

            # Categorize error type for better monitoring
            error_type = self._categorize_error(e)

            error_attributes = {
                "model": model,
                "status": "error",
                "error_type": error_type,
            }
            if operation:
                error_attributes["operation"] = operation

            # Record error in metrics
            llm_request_duration.record(duration_ms, attributes=error_attributes)
            llm_request_total.add(1, attributes=error_attributes)
            llm_errors_total.add(1, attributes=error_attributes)

            # Add error attributes to span
            if span.is_recording():
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.request.duration_ms", duration_ms)
                span.set_attribute("llm.error.type", error_type)
                span.set_attribute("llm.error.message", str(e))
                if operation:
                    span.set_attribute("llm.operation", operation)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            # Log error with categorization
            logger.error(
                f"LLM request failed: operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"error_type={error_type}, error={type(e).__name__}: {str(e)}"
            )

            raise

    def _categorize_error(self, error: Exception) -> str:
        """
        Categorize OpenAI errors into monitoring-friendly types.

        Returns:
            str: Error category (insufficient_funds, timeout, rate_limit, api_error, unknown)
        """
        error_message = str(error).lower()

        # Check for insufficient funds (CRITICAL - circuit breaker trigger)
        if "insufficient" in error_message and "quota" in error_message:
            return "insufficient_funds"
        if "quota" in error_message and "exceeded" in error_message:
            return "insufficient_funds"

        # Check for timeout errors
        if isinstance(error, APITimeoutError):
            return "timeout"
        if "timeout" in error_message:
            return "timeout"

        # Check for rate limiting
        if isinstance(error, RateLimitError):
            return "rate_limit"
        if "rate limit" in error_message or "rate_limit" in error_message:
            return "rate_limit"

        # General API errors
        if isinstance(error, APIError):
            return "api_error"

        # Unknown/unexpected errors
        return "unknown"

    def _clean_response(self, raw_content: str) -> str:
        """Clean LLM response by removing markdown code blocks."""
        if not raw_content:
            return raw_content

        cleaned = raw_content.strip()

        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove ```

        return cleaned.strip()
