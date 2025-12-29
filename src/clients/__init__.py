"""External service clients.

Provides a unified interface for LLM clients (OpenAI, Gemini) via factory.
"""

from src.clients.abstract_llm_client import AbstractLLMClient
from src.clients.llm_client_factory import get_client

# Lazy imports - only import when actually used to avoid
# requiring all provider SDKs to be installed
__all__ = [
    "AbstractLLMClient",
    "get_client",
]
