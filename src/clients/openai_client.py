import logging
import time

from openai import AsyncOpenAI
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
    """Async client for OpenAI."""

    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def handle_request(self, prompt: str, operation: str | None = None) -> str:
        """
        Send a chat completion request to OpenAI and return the content string.

        Args:
            prompt: The prompt to send to OpenAI
            operation: Optional operation name for metrics (e.g., "problem_generation", "sentence_validation")

        Returns:
            Cleaned response content
        """
        model = "gpt-4o-mini"
        start_time = time.time()
        status = "success"

        # Get current span for adding attributes
        span = trace.get_current_span()

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )

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
            error_attributes = {
                "model": model,
                "status": "error",
                "error_type": type(e).__name__,
            }
            if operation:
                error_attributes["operation"] = operation

            llm_request_duration.record(duration_ms, attributes=error_attributes)
            llm_request_total.add(1, attributes=error_attributes)

            # Add error attributes to span
            if span.is_recording():
                span.set_attribute("llm.model", model)
                span.set_attribute("llm.request.duration_ms", duration_ms)
                span.set_attribute("llm.error.type", type(e).__name__)
                span.set_attribute("llm.error.message", str(e))
                if operation:
                    span.set_attribute("llm.operation", operation)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

            # Log error
            logger.error(
                f"LLM request failed: operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"error={type(e).__name__}: {str(e)}"
            )

            raise

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
