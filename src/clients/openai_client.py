"""OpenAI client with observability and metadata capture.

Handles both reasoning models (gpt-5) via Responses API and standard models
(gpt-4o-mini) via Chat Completions, returning LLMResponse with full metadata
including reasoning summaries when available.
"""

import logging
import time
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from opentelemetry import metrics, trace

from src.clients.abstract_llm_client import AbstractLLMClient
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


class OpenAIClient(AbstractLLMClient):
    """Async client for OpenAI with timeout, retry protection, and full observability.

    Uses the Responses API for reasoning models (gpt-5) to capture reasoning summaries,
    and Chat Completions API for standard models (gpt-4o-mini).
    """

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            timeout=120.0,
            max_retries=1,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    async def handle_request(
        self,
        prompt: str,
        model: str,
        operation: str | None = None,
        response_format: dict[str, Any] | None = None,
        use_reasoning: bool = True,
    ) -> LLMResponse:
        """Send a request to OpenAI.

        Routes to Responses API for reasoning models (gpt-5) or Chat Completions
        for standard models (gpt-4o-mini).

        Args:
            prompt: The prompt to send to OpenAI
            model: The model to use (e.g., "gpt-4o-mini", "gpt-5-nano-2025-08-07")
            operation: Optional operation name for metrics
            response_format: Optional JSON schema for structured output
            use_reasoning: Whether to use reasoning mode (Responses API for gpt-5)

        Returns:
            LLMResponse with content and metadata (reasoning summary for gpt-5)
        """
        is_reasoning_model = use_reasoning and "gpt-5" in model.lower()

        if is_reasoning_model:
            return await self._handle_responses_api(
                prompt, model, operation, response_format
            )
        else:
            return await self._handle_chat_completions(
                prompt, model, operation, response_format
            )

    async def _handle_responses_api(
        self,
        prompt: str,
        model: str,
        operation: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Handle request using Responses API (for reasoning models).

        The Responses API provides reasoning summaries for gpt-5 models.
        """
        start_time = time.time()
        span = trace.get_current_span()

        try:
            # Build request parameters for Responses API
            request_params: dict[str, Any] = {
                "model": model,
                "input": prompt,
                "reasoning": {"effort": "medium", "summary": "auto"},
                "service_tier": "priority",
            }

            # Add structured output if provided
            if response_format:
                # Responses API uses 'text' parameter for structured output
                request_params["text"] = {"format": response_format}

            response = await self.client.responses.create(**request_params)
            duration_ms = (time.time() - start_time) * 1000

            # Extract content and reasoning from output items
            content = None
            reasoning_content = None

            for item in response.output:
                if item.type == "reasoning":
                    # Extract reasoning summary
                    if hasattr(item, "summary") and item.summary:
                        reasoning_parts = []
                        for summary_item in item.summary:
                            if hasattr(summary_item, "text"):
                                reasoning_parts.append(summary_item.text)
                        if reasoning_parts:
                            reasoning_content = "\n\n".join(reasoning_parts)
                elif item.type == "message":
                    # Extract message content
                    if hasattr(item, "content") and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, "text"):
                                content = content_item.text
                                break

            # Extract usage information
            usage = response.usage
            prompt_tokens = usage.input_tokens if usage else 0
            completion_tokens = usage.output_tokens if usage else 0
            total_tokens = usage.input_tokens + usage.output_tokens if usage else 0

            # Extract reasoning tokens
            reasoning_tokens = None
            if usage and hasattr(usage, "output_tokens_details"):
                details = usage.output_tokens_details
                if details and hasattr(details, "reasoning_tokens"):
                    reasoning_tokens = details.reasoning_tokens

            # Record metrics and log
            self._record_metrics(
                model=model,
                operation=operation,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                reasoning_tokens=reasoning_tokens,
                status="success",
                span=span,
                response_id=response.id,
            )

            # Log with reasoning summary preview
            reasoning_log = (
                f", reasoning={reasoning_tokens}" if reasoning_tokens else ""
            )
            summary_preview = ""
            if reasoning_content:
                preview = reasoning_content[:100].replace("\n", " ")
                summary_preview = f', summary="{preview}..."'

            logger.info(
                f"LLM request completed (Responses API): operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"tokens=(prompt={prompt_tokens}, completion={completion_tokens}, "
                f"total={total_tokens}{reasoning_log}){summary_preview}"
            )

            return LLMResponse(
                content=self._clean_response(content),
                model=model,
                response_id=response.id,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                reasoning_tokens=reasoning_tokens,
                reasoning_content=reasoning_content,
                raw_content=content,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._handle_error(e, model, operation, duration_ms, span)
            raise

    async def _handle_chat_completions(
        self,
        prompt: str,
        model: str,
        operation: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Handle request using Chat Completions API (for standard models)."""
        start_time = time.time()
        span = trace.get_current_span()

        try:
            # Build request parameters
            request_params: dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "service_tier": "priority",
            }

            if response_format:
                request_params["response_format"] = response_format

            response = await self.client.chat.completions.create(**request_params)
            duration_ms = (time.time() - start_time) * 1000

            # Extract usage information
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            # Record metrics and log
            self._record_metrics(
                model=model,
                operation=operation,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                reasoning_tokens=None,
                status="success",
                span=span,
                response_id=response.id,
            )

            logger.info(
                f"LLM request completed (Chat Completions): operation={operation or 'unknown'}, "
                f"model={model}, duration={duration_ms:.0f}ms, "
                f"tokens=(prompt={prompt_tokens}, completion={completion_tokens}, "
                f"total={total_tokens})"
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
                reasoning_tokens=None,
                reasoning_content=None,
                raw_content=raw_content,
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
        reasoning_tokens: int | None,
        status: str,
        span: Any,
        response_id: str,
    ) -> None:
        """Record OpenTelemetry metrics and span attributes."""
        attributes = {"model": model, "status": status}
        if operation:
            attributes["operation"] = operation

        llm_request_duration.record(duration_ms, attributes=attributes)
        llm_request_total.add(1, attributes=attributes)

        if prompt_tokens or completion_tokens:
            llm_tokens_input.add(prompt_tokens, attributes=attributes)
            llm_tokens_output.add(completion_tokens, attributes=attributes)
            llm_tokens_total.add(total_tokens, attributes=attributes)

        if reasoning_tokens:
            llm_tokens_reasoning.add(reasoning_tokens, attributes=attributes)

        if span.is_recording():
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.request.duration_ms", duration_ms)
            span.set_attribute("llm.response.id", response_id)
            span.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
            span.set_attribute("llm.usage.completion_tokens", completion_tokens)
            span.set_attribute("llm.usage.total_tokens", total_tokens)
            if operation:
                span.set_attribute("llm.operation", operation)
            if reasoning_tokens is not None:
                span.set_attribute("llm.usage.reasoning_tokens", reasoning_tokens)

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
