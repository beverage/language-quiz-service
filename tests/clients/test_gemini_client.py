"""Unit tests for GeminiClient."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.gemini_client import GeminiClient


@pytest.fixture
def mock_gemini_response():
    """Create a mock Gemini response."""
    mock_response = MagicMock()

    # Mock candidate with thinking and regular content
    mock_thinking_part = MagicMock()
    mock_thinking_part.thought = True
    mock_thinking_part.text = "Let me think about this..."

    mock_content_part = MagicMock()
    mock_content_part.thought = False
    mock_content_part.text = '{"result": "test response"}'

    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_thinking_part, mock_content_part]

    mock_response.candidates = [mock_candidate]

    # Mock usage metadata
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 100
    mock_usage.candidates_token_count = 50
    mock_usage.total_token_count = 150
    mock_usage.thoughts_token_count = 25
    mock_response.usage_metadata = mock_usage

    return mock_response


@pytest.mark.asyncio
async def test_handle_request_with_thinking(mock_gemini_response):
    """Test GeminiClient.handle_request with thinking enabled."""
    with (
        patch("src.clients.gemini_client.genai.Client") as mock_client_class,
        patch("src.clients.gemini_client.trace.get_current_span") as mock_span,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            return_value=mock_gemini_response
        )
        mock_client_class.return_value = mock_client

        mock_span_instance = MagicMock()
        mock_span_instance.is_recording.return_value = True
        mock_span.return_value = mock_span_instance

        # Create client and make request
        client = GeminiClient(api_key="test-key")
        result = await client.handle_request(
            prompt="Test prompt",
            model="gemini-2.5-flash",
            operation="test_operation",
            use_reasoning=True,
        )

        # Verify response
        assert result.content == '{"result": "test response"}'
        assert result.model == "gemini-2.5-flash"
        assert result.prompt_tokens == 100
        assert result.completion_tokens == 50
        assert result.total_tokens == 150
        assert result.reasoning_tokens == 25
        assert result.reasoning_content == "Let me think about this..."

        # Verify generate_content was called
        mock_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_handle_request_without_thinking(mock_gemini_response):
    """Test GeminiClient.handle_request with thinking disabled."""
    with (
        patch("src.clients.gemini_client.genai.Client") as mock_client_class,
        patch("src.clients.gemini_client.trace.get_current_span") as mock_span,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            return_value=mock_gemini_response
        )
        mock_client_class.return_value = mock_client

        mock_span_instance = MagicMock()
        mock_span_instance.is_recording.return_value = True
        mock_span.return_value = mock_span_instance

        # Create client and make request
        client = GeminiClient(api_key="test-key")
        await client.handle_request(
            prompt="Test prompt",
            model="gemini-2.5-flash",
            operation="test_operation",
            use_reasoning=False,
        )

        # Verify generate_content was called
        call_kwargs = mock_client.aio.models.generate_content.call_args
        config = call_kwargs.kwargs["config"]

        # When use_reasoning=False, thinking_budget should be 0
        assert config.thinking_config.thinking_budget == 0


@pytest.mark.asyncio
async def test_provider_name():
    """Test GeminiClient.provider_name property."""
    with patch("src.clients.gemini_client.genai.Client"):
        client = GeminiClient(api_key="test-key")
        assert client.provider_name == "gemini"


@pytest.mark.asyncio
async def test_handle_request_logs_success(mock_gemini_response, caplog):
    """Test that successful requests are logged."""
    caplog.set_level(logging.INFO, logger="src.clients.gemini_client")

    with (
        patch("src.clients.gemini_client.genai.Client") as mock_client_class,
        patch("src.clients.gemini_client.trace.get_current_span") as mock_span,
    ):
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            return_value=mock_gemini_response
        )
        mock_client_class.return_value = mock_client

        mock_span_instance = MagicMock()
        mock_span_instance.is_recording.return_value = False
        mock_span.return_value = mock_span_instance

        client = GeminiClient(api_key="test-key")
        await client.handle_request(
            prompt="Test prompt",
            model="gemini-2.5-flash",
            operation="test_log",
        )

        # Check for success log
        assert any(
            "LLM request completed (Gemini)" in r.message for r in caplog.records
        )
        assert any("test_log" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_handle_request_error_handling():
    """Test error handling in GeminiClient."""
    with (
        patch("src.clients.gemini_client.genai.Client") as mock_client_class,
        patch("src.clients.gemini_client.trace.get_current_span") as mock_span,
    ):
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API Error")
        )
        mock_client_class.return_value = mock_client

        mock_span_instance = MagicMock()
        mock_span_instance.is_recording.return_value = True
        mock_span.return_value = mock_span_instance

        client = GeminiClient(api_key="test-key")

        with pytest.raises(Exception, match="API Error"):
            await client.handle_request(
                prompt="Test prompt",
                model="gemini-2.5-flash",
            )


def test_clean_response():
    """Test response cleaning."""
    with patch("src.clients.gemini_client.genai.Client"):
        client = GeminiClient(api_key="test-key")

        # Test markdown code block removal
        assert client._clean_response("```json\n{}\n```") == "{}"
        assert client._clean_response("```\ntest\n```") == "test"
        assert client._clean_response("plain text") == "plain text"
        assert client._clean_response(None) == ""
        assert client._clean_response("") == ""


def test_error_categorization():
    """Test error categorization."""
    with patch("src.clients.gemini_client.genai.Client"):
        client = GeminiClient(api_key="test-key")

        assert client._categorize_error(Exception("quota exceeded")) == "quota_exceeded"
        assert client._categorize_error(Exception("timeout")) == "timeout"
        assert client._categorize_error(Exception("rate limit")) == "rate_limit"
        assert (
            client._categorize_error(Exception("invalid api key")) == "invalid_api_key"
        )
        assert (
            client._categorize_error(Exception("permission denied"))
            == "permission_denied"
        )
        assert client._categorize_error(Exception("random error")) == "unknown"
