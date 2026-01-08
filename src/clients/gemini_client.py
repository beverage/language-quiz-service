"""Gemini client with observability and thinking support.

Uses Google's genai SDK to make requests to Gemini models, with full
thinking content capture when enabled.
"""

import logging
import time
from typing import Any

from google import genai
from google.genai import types
from opentelemetry import metrics, trace

from src.clients.abstract_llm_client import AbstractLLMClient
from src.clients.schema_converter import convert_openai_format_to_genai_schema
from src.core.config import settings
from src.schemas.llm_response import LLMResponse

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry meter for custom LLM metrics
meter = metrics.get_meter(__name__)

llm_request_duration = meter.create_histogram(
    name="llm.request.duration",
    unit="ms",
    description="Duration of LLM API requests",
    explicit_bucket_boundaries_advisory=[1000, 5000, 10000, 20000, 30000, 60000],
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
    description="Total reasoning/thinking tokens consumed (Gemini models)",
)


class GeminiClient(AbstractLLMClient):
    """Async client for Google Gemini with thinking support and observability.

    Uses the google-genai SDK with thinking_config to capture full reasoning
    traces for debugging and analysis.
    """

    def __init__(self, api_key: str | None = None):
        self.client = genai.Client(api_key=api_key or settings.gemini_api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def handle_request(
        self,
        prompt: str,
        model: str,
        operation: str | None = None,
        response_format: dict[str, Any] | None = None,
        use_reasoning: bool = True,
    ) -> LLMResponse:
        """Send a request to Gemini.

        Args:
            prompt: The prompt to send
            model: The model to use (e.g., "gemini-2.5-flash")
            operation: Optional operation name for metrics
            response_format: Optional JSON schema for structured output
            use_reasoning: Whether to enable thinking mode (thinking_budget=-1)

        Returns:
            LLMResponse with content and metadata (thinking content when enabled)
        """
        start_time = time.time()
        span = trace.get_current_span()

        try:
            # Build generation config
            config_params: dict[str, Any] = {}

            # Configure thinking based on use_reasoning flag
            if use_reasoning:
                config_params["thinking_config"] = types.ThinkingConfig(
                    thinking_budget=1500,  # Auto
                    include_thoughts=True,
                )
            else:
                config_params["thinking_config"] = types.ThinkingConfig(
                    thinking_budget=0,  # Disabled
                )

            # Add structured output if provided (convert from OpenAI format)
            if response_format:
                gemini_schema = convert_openai_format_to_genai_schema(response_format)
                if gemini_schema:
                    config_params["response_mime_type"] = "application/json"
                    config_params["response_schema"] = gemini_schema
                else:
                    logger.warning(
                        "Failed to convert response_format to Gemini schema, "
                        "proceeding without structured output"
                    )

            # Make the API call
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params),
            )

            duration_ms = (time.time() - start_time) * 1000

            # Extract content and thinking from response
            content = None
            thinking_content = None

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "thought") and part.thought:
                            # This is a thinking part
                            if hasattr(part, "text") and part.text:
                                if thinking_content:
                                    thinking_content += "\n\n" + part.text
                                else:
                                    thinking_content = part.text
                        elif hasattr(part, "text") and part.text:
                            # Regular content part
                            if content:
                                content += part.text
                            else:
                                content = part.text

            # Extract usage information
            usage = response.usage_metadata
            prompt_tokens = usage.prompt_token_count if usage else 0
            completion_tokens = usage.candidates_token_count if usage else 0
            total_tokens = usage.total_token_count if usage else 0

            # Extract thinking tokens if available
            thinking_tokens = None
            if usage:
                # Try multiple possible attribute names for thinking tokens
                if (
                    hasattr(usage, "thoughts_token_count")
                    and usage.thoughts_token_count is not None
                ):
                    thinking_tokens = usage.thoughts_token_count
                elif (
                    hasattr(usage, "thinking_token_count")
                    and usage.thinking_token_count is not None
                ):
                    thinking_tokens = usage.thinking_token_count
                elif (
                    hasattr(usage, "reasoning_token_count")
                    and usage.reasoning_token_count is not None
                ):
                    thinking_tokens = usage.reasoning_token_count

            # Generate a response ID (Gemini doesn't provide one like OpenAI)
            response_id = f"gemini-{int(time.time() * 1000)}"

            # Record metrics
            self._record_metrics(
                model=model,
                operation=operation,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                thinking_tokens=thinking_tokens,
                status="success",
                span=span,
                response_id=response_id,
            )

            # Log with thinking preview
            thinking_log = f", thinking={thinking_tokens}" if thinking_tokens else ""
            thinking_preview = ""
            if thinking_content:
                preview = thinking_content[:100].replace("\n", " ")
                thinking_preview = f', thinking_preview="{preview}..."'

            logger.info(
                f"LLM request completed (Gemini): operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"tokens=(prompt={prompt_tokens}, completion={completion_tokens}, "
                f"total={total_tokens}{thinking_log}){thinking_preview}"
            )

            return LLMResponse(
                content=self._clean_response(content),
                model=model,
                response_id=response_id,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                reasoning_tokens=thinking_tokens,
                reasoning_content=thinking_content,
                raw_content=content,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._handle_error(e, model, operation, duration_ms, span)
            raise

    def _record_metrics(
        self,
        model: str,
        operation: str | None,
        duration_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        thinking_tokens: int | None,
        status: str,
        span: Any,
        response_id: str,
    ) -> None:
        """Record OpenTelemetry metrics and span attributes."""
        attributes = {"model": model, "status": status, "provider": "gemini"}
        if operation:
            attributes["operation"] = operation

        llm_request_duration.record(duration_ms, attributes=attributes)
        llm_request_total.add(1, attributes=attributes)

        if prompt_tokens or completion_tokens:
            llm_tokens_input.add(prompt_tokens, attributes=attributes)
            llm_tokens_output.add(completion_tokens, attributes=attributes)
            llm_tokens_total.add(total_tokens, attributes=attributes)

        if thinking_tokens is not None and thinking_tokens > 0:
            llm_tokens_reasoning.add(thinking_tokens, attributes=attributes)
            logger.debug(
                f"Recorded reasoning tokens: {thinking_tokens} for model={model}, "
                f"operation={operation or 'unknown'}, attributes={attributes}"
            )

        if span.is_recording():
            span.set_attribute("llm.provider", "gemini")
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.request.duration_ms", duration_ms)
            span.set_attribute("llm.response.id", response_id)
            span.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
            span.set_attribute("llm.usage.completion_tokens", completion_tokens)
            span.set_attribute("llm.usage.total_tokens", total_tokens)
            if operation:
                span.set_attribute("llm.operation", operation)
            if thinking_tokens is not None:
                span.set_attribute("llm.usage.thinking_tokens", thinking_tokens)

    def _handle_error(
        self,
        error: Exception,
        model: str,
        operation: str | None,
        duration_ms: float,
        span: Any,
    ) -> None:
        """Handle and record error metrics."""
        error_type = self._categorize_error(error)

        error_attributes = {
            "model": model,
            "status": "error",
            "error_type": error_type,
            "provider": "gemini",
        }
        if operation:
            error_attributes["operation"] = operation

        llm_request_duration.record(duration_ms, attributes=error_attributes)
        llm_request_total.add(1, attributes=error_attributes)
        llm_errors_total.add(1, attributes=error_attributes)

        if span.is_recording():
            span.set_attribute("llm.provider", "gemini")
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.request.duration_ms", duration_ms)
            span.set_attribute("llm.error.type", error_type)
            span.set_attribute("llm.error.message", str(error))
            if operation:
                span.set_attribute("llm.operation", operation)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))

        logger.error(
            f"LLM request failed: operation={operation or 'unknown'}, "
            f"model={model}, duration={duration_ms:.0f}ms, "
            f"error_type={error_type}, error={type(error).__name__}: {str(error)}"
        )

    def _categorize_error(self, error: Exception) -> str:
        """Categorize Gemini errors into monitoring-friendly types."""
        error_message = str(error).lower()

        if "quota" in error_message:
            return "quota_exceeded"
        if "timeout" in error_message:
            return "timeout"
        if "rate" in error_message and "limit" in error_message:
            return "rate_limit"
        if "invalid" in error_message and "api" in error_message:
            return "invalid_api_key"
        if "permission" in error_message or "forbidden" in error_message:
            return "permission_denied"
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
