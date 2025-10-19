"""Unit tests for OpenAI client with observability features.

These tests verify that LLM calls properly record metrics, span attributes,
and logs for performance monitoring and debugging.
"""

import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage

from src.clients.openai_client import OpenAIClient


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI response with usage data."""
    return ChatCompletion(
        id=f"chatcmpl-{uuid4().hex[:8]}",
        created=int(time.time()),
        model="gpt-4o-mini",
        object="chat.completion",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content="Test response content",
                    role="assistant",
                ),
            )
        ],
        usage=CompletionUsage(
            prompt_tokens=50,
            completion_tokens=25,
            total_tokens=75,
        ),
    )


@pytest.fixture
def mock_openai_response_no_usage():
    """Create a mock OpenAI response without usage data."""
    return ChatCompletion(
        id=f"chatcmpl-{uuid4().hex[:8]}",
        created=int(time.time()),
        model="gpt-4o-mini",
        object="chat.completion",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content="Test response content",
                    role="assistant",
                ),
            )
        ],
        usage=None,
    )


@pytest.fixture
def mock_metrics():
    """Mock OpenTelemetry metrics."""
    with (
        patch("src.clients.openai_client.llm_request_duration") as duration,
        patch("src.clients.openai_client.llm_request_total") as total,
        patch("src.clients.openai_client.llm_tokens_input") as tokens_in,
        patch("src.clients.openai_client.llm_tokens_output") as tokens_out,
        patch("src.clients.openai_client.llm_tokens_total") as tokens_total,
    ):
        yield {
            "duration": duration,
            "total": total,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
            "tokens_total": tokens_total,
        }


@pytest.fixture
def mock_span():
    """Mock OpenTelemetry span."""
    span = MagicMock()
    span.is_recording.return_value = True
    span.set_attribute = MagicMock()
    span.set_status = MagicMock()
    return span


@pytest.mark.asyncio
async def test_handle_request_records_metrics(
    mock_openai_response, mock_metrics, mock_span
):
    """Test that successful LLM requests record all metrics correctly."""
    client = OpenAIClient(api_key="test-key")

    # Mock the AsyncOpenAI client
    client.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    # Mock span and trace
    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        result = await client.handle_request("Test prompt", operation="test_operation")

    # Verify response
    assert result == "Test response content"

    # Verify duration metric was recorded
    mock_metrics["duration"].record.assert_called_once()
    duration_call = mock_metrics["duration"].record.call_args
    assert duration_call[0][0] > 0  # Duration should be positive
    assert duration_call[1]["attributes"]["model"] == "gpt-4o-mini"
    assert duration_call[1]["attributes"]["status"] == "success"
    assert duration_call[1]["attributes"]["operation"] == "test_operation"

    # Verify request counter was incremented
    mock_metrics["total"].add.assert_called_once_with(
        1,
        attributes={
            "model": "gpt-4o-mini",
            "status": "success",
            "operation": "test_operation",
        },
    )

    # Verify token metrics were recorded
    mock_metrics["tokens_input"].add.assert_called_once_with(
        50,
        attributes={
            "model": "gpt-4o-mini",
            "status": "success",
            "operation": "test_operation",
        },
    )
    mock_metrics["tokens_output"].add.assert_called_once_with(
        25,
        attributes={
            "model": "gpt-4o-mini",
            "status": "success",
            "operation": "test_operation",
        },
    )
    mock_metrics["tokens_total"].add.assert_called_once_with(
        75,
        attributes={
            "model": "gpt-4o-mini",
            "status": "success",
            "operation": "test_operation",
        },
    )


@pytest.mark.asyncio
async def test_handle_request_sets_span_attributes(
    mock_openai_response, mock_metrics, mock_span
):
    """Test that LLM requests set proper span attributes for tracing."""
    client = OpenAIClient(api_key="test-key")
    client.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        await client.handle_request("Test prompt", operation="sentence_validation")

    # Verify span attributes were set
    span_attributes = {
        call[0][0]: call[0][1] for call in mock_span.set_attribute.call_args_list
    }

    assert span_attributes["llm.model"] == "gpt-4o-mini"
    assert span_attributes["llm.operation"] == "sentence_validation"
    assert span_attributes["llm.request.duration_ms"] > 0
    assert span_attributes["llm.response.id"] == mock_openai_response.id
    assert span_attributes["llm.usage.prompt_tokens"] == 50
    assert span_attributes["llm.usage.completion_tokens"] == 25
    assert span_attributes["llm.usage.total_tokens"] == 75


@pytest.mark.asyncio
async def test_handle_request_without_operation(
    mock_openai_response, mock_metrics, mock_span
):
    """Test that LLM requests work without an operation parameter."""
    client = OpenAIClient(api_key="test-key")
    client.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        result = await client.handle_request("Test prompt")

    # Verify response
    assert result == "Test response content"

    # Verify metrics don't include operation
    duration_call = mock_metrics["duration"].record.call_args
    assert "operation" not in duration_call[1]["attributes"]

    # Verify span doesn't have operation attribute
    span_attribute_names = [
        call[0][0] for call in mock_span.set_attribute.call_args_list
    ]
    assert "llm.operation" not in span_attribute_names


@pytest.mark.asyncio
async def test_handle_request_without_usage_data(
    mock_openai_response_no_usage, mock_metrics, mock_span
):
    """Test that LLM requests handle responses without usage data gracefully."""
    client = OpenAIClient(api_key="test-key")
    client.client.chat.completions.create = AsyncMock(
        return_value=mock_openai_response_no_usage
    )

    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        result = await client.handle_request("Test prompt", operation="test_op")

    # Verify response
    assert result == "Test response content"

    # Verify token metrics were NOT called (since usage is None)
    mock_metrics["tokens_input"].add.assert_not_called()
    mock_metrics["tokens_output"].add.assert_not_called()
    mock_metrics["tokens_total"].add.assert_not_called()

    # Verify span attributes show 0 tokens (still set even without usage data)
    span_attributes = {
        call[0][0]: call[0][1] for call in mock_span.set_attribute.call_args_list
    }
    assert span_attributes["llm.usage.prompt_tokens"] == 0
    assert span_attributes["llm.usage.completion_tokens"] == 0
    assert span_attributes["llm.usage.total_tokens"] == 0


@pytest.mark.asyncio
async def test_handle_request_error_records_metrics(mock_metrics, mock_span):
    """Test that failed LLM requests record error metrics and span attributes."""
    client = OpenAIClient(api_key="test-key")

    # Mock an error (using message that won't be categorized)
    error = Exception("API connection failed")
    client.client.chat.completions.create = AsyncMock(side_effect=error)

    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        with pytest.raises(Exception, match="API connection failed"):
            await client.handle_request("Test prompt", operation="test_operation")

    # Verify error metrics were recorded
    duration_call = mock_metrics["duration"].record.call_args
    assert duration_call[0][0] > 0  # Duration should be positive
    assert duration_call[1]["attributes"]["model"] == "gpt-4o-mini"
    assert duration_call[1]["attributes"]["status"] == "error"
    assert duration_call[1]["attributes"]["operation"] == "test_operation"
    assert duration_call[1]["attributes"]["error_type"] == "unknown"

    # Verify error counter was incremented
    mock_metrics["total"].add.assert_called_once_with(
        1,
        attributes={
            "model": "gpt-4o-mini",
            "status": "error",
            "operation": "test_operation",
            "error_type": "unknown",
        },
    )

    # Verify span error attributes were set
    span_attributes = {
        call[0][0]: call[0][1] for call in mock_span.set_attribute.call_args_list
    }
    assert span_attributes["llm.model"] == "gpt-4o-mini"
    assert span_attributes["llm.operation"] == "test_operation"
    assert span_attributes["llm.error.type"] == "unknown"
    assert span_attributes["llm.error.message"] == "API connection failed"

    # Verify span status was set to error
    mock_span.set_status.assert_called_once()


@pytest.mark.asyncio
async def test_handle_request_logs_success(
    mock_openai_response, mock_metrics, mock_span, caplog
):
    """Test that successful LLM requests are logged with token usage."""
    import logging

    # Set log level to capture INFO messages
    caplog.set_level(logging.INFO, logger="src.clients.openai_client")

    client = OpenAIClient(api_key="test-key")
    client.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        await client.handle_request("Test prompt", operation="verb_analysis")

    # Verify log message
    assert "LLM request completed" in caplog.text
    assert "operation=verb_analysis" in caplog.text
    assert "model=gpt-4o-mini" in caplog.text
    assert "tokens=(prompt=50, completion=25, total=75)" in caplog.text


@pytest.mark.asyncio
async def test_handle_request_logs_error(mock_metrics, mock_span, caplog):
    """Test that failed LLM requests are logged with error details."""
    import logging

    # Set log level to capture ERROR messages
    caplog.set_level(logging.ERROR, logger="src.clients.openai_client")

    client = OpenAIClient(api_key="test-key")

    error = ValueError("Invalid request")
    client.client.chat.completions.create = AsyncMock(side_effect=error)

    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        with pytest.raises(ValueError):
            await client.handle_request("Test prompt", operation="sentence_generation")

    # Verify error log message
    assert "LLM request failed" in caplog.text
    assert "operation=sentence_generation" in caplog.text
    assert "model=gpt-4o-mini" in caplog.text
    assert "error=ValueError: Invalid request" in caplog.text


@pytest.mark.asyncio
async def test_clean_response_removes_markdown():
    """Test that response cleaning removes markdown code blocks."""
    client = OpenAIClient(api_key="test-key")

    # Test removing ```json
    assert (
        client._clean_response('```json\n{"key": "value"}\n```') == '{"key": "value"}'
    )

    # Test removing ```
    assert client._clean_response('```\n{"key": "value"}\n```') == '{"key": "value"}'

    # Test no markdown
    assert client._clean_response('{"key": "value"}') == '{"key": "value"}'

    # Test empty string
    assert client._clean_response("") == ""

    # Test None
    assert client._clean_response(None) is None


@pytest.mark.asyncio
async def test_span_not_recording(mock_openai_response, mock_metrics):
    """Test that span attributes are not set when span is not recording."""
    mock_span = MagicMock()
    mock_span.is_recording.return_value = False

    client = OpenAIClient(api_key="test-key")
    client.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    with patch(
        "src.clients.openai_client.trace.get_current_span", return_value=mock_span
    ):
        await client.handle_request("Test prompt", operation="test_op")

    # Verify span attributes were not set
    mock_span.set_attribute.assert_not_called()
