"""Abstract base class for LLM clients.

Defines the common interface for all LLM providers (OpenAI, Gemini, etc.)
ensuring consistent behavior across providers.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.schemas.llm_response import LLMResponse


class AbstractLLMClient(ABC):
    """Abstract base class for LLM client implementations.

    All LLM providers must implement this interface to ensure consistent
    behavior across the application. The factory uses this to provide
    the appropriate client based on configuration.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'openai', 'gemini')."""
        ...

    @abstractmethod
    async def handle_request(
        self,
        prompt: str,
        model: str,
        operation: str | None = None,
        response_format: dict[str, Any] | None = None,
        use_reasoning: bool = True,
    ) -> LLMResponse:
        """Send a request to the LLM provider.

        Args:
            prompt: The prompt to send
            model: The model identifier to use
            operation: Optional operation name for metrics/tracing
            response_format: Optional JSON schema for structured output
            use_reasoning: Whether to enable reasoning/thinking mode

        Returns:
            LLMResponse with content, metadata, and optional reasoning trace
        """
        ...
