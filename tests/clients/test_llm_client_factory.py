"""Tests for LLM client factory."""

from unittest.mock import patch

import pytest

from src.clients.llm_client_factory import get_client


@pytest.mark.unit
class TestLLMClientFactory:
    """Test LLM client factory functionality."""

    def test_get_client_returns_openai_client(self):
        """Test that get_client returns OpenAI client when LLM_PROVIDER is 'openai'."""
        with patch("src.clients.llm_client_factory.settings") as mock_settings:
            mock_settings.llm_provider = "openai"

            client = get_client()

            assert client is not None
            assert client.provider_name == "openai"

    def test_get_client_returns_gemini_client(self):
        """Test that get_client returns Gemini client when LLM_PROVIDER is 'gemini'."""
        with patch("src.clients.llm_client_factory.settings") as mock_settings:
            mock_settings.llm_provider = "gemini"

            client = get_client()

            assert client is not None
            assert client.provider_name == "gemini"

    def test_get_client_case_insensitive_openai(self):
        """Test that get_client is case-insensitive for 'openai'."""
        with patch("src.clients.llm_client_factory.settings") as mock_settings:
            mock_settings.llm_provider = "OPENAI"

            client = get_client()

            assert client is not None
            assert client.provider_name == "openai"

    def test_get_client_case_insensitive_gemini(self):
        """Test that get_client is case-insensitive for 'gemini'."""
        with patch("src.clients.llm_client_factory.settings") as mock_settings:
            mock_settings.llm_provider = "GEMINI"

            client = get_client()

            assert client is not None
            assert client.provider_name == "gemini"

    def test_get_client_mixed_case(self):
        """Test that get_client handles mixed case."""
        with patch("src.clients.llm_client_factory.settings") as mock_settings:
            mock_settings.llm_provider = "OpenAI"

            client = get_client()

            assert client is not None
            assert client.provider_name == "openai"

    def test_get_client_raises_value_error_for_invalid_provider(self):
        """Test that get_client raises ValueError for invalid provider."""
        with patch("src.clients.llm_client_factory.settings") as mock_settings:
            mock_settings.llm_provider = "invalid_provider"

            with pytest.raises(ValueError) as exc_info:
                get_client()

            assert "Unknown LLM provider" in str(exc_info.value)
            assert "invalid_provider" in str(exc_info.value)
            assert "Set LLM_PROVIDER to 'openai' or 'gemini'" in str(exc_info.value)

    def test_get_client_raises_value_error_for_empty_provider(self):
        """Test that get_client raises ValueError for empty provider."""
        with patch("src.clients.llm_client_factory.settings") as mock_settings:
            mock_settings.llm_provider = ""

            with pytest.raises(ValueError) as exc_info:
                get_client()

            assert "Unknown LLM provider" in str(exc_info.value)
