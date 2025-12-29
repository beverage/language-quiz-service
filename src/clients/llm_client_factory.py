"""Factory for creating LLM clients based on configuration.

Uses the LLM_PROVIDER environment variable to determine which provider
to use (openai or gemini).
"""

from src.clients.abstract_llm_client import AbstractLLMClient
from src.core.config import settings


def get_client() -> AbstractLLMClient:
    """Get the configured LLM client based on LLM_PROVIDER setting.

    Returns:
        AbstractLLMClient: The configured LLM client (OpenAI or Gemini)

    Raises:
        ValueError: If LLM_PROVIDER is not 'openai' or 'gemini'
    """
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        from src.clients.gemini_client import GeminiClient

        return GeminiClient()
    elif provider == "openai":
        from src.clients.openai_client import OpenAIClient

        return OpenAIClient()
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            "Set LLM_PROVIDER to 'openai' or 'gemini'."
        )
