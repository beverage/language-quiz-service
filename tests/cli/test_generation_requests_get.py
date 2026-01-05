"""Tests for CLI generation-request get command."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from asyncclick.testing import CliRunner

from src.cli.generation_requests.commands import get_request
from src.schemas.generation_requests import EntityType, GenerationStatus


@pytest.fixture
def sample_generation_response():
    """Sample generation request response with problems."""
    return {
        "request_id": "87654321-4321-8765-4321-876543218765",
        "status": GenerationStatus.COMPLETED.value,
        "entity_type": EntityType.PROBLEM.value,
        "requested_count": 2,
        "generated_count": 2,
        "failed_count": 0,
        "requested_at": "2023-01-01T12:00:00Z",
        "completed_at": "2023-01-01T12:05:00Z",
        "entities": [
            {
                "id": "12345678-1234-5678-1234-567812345678",
                "problem_type": "grammar",
                "title": "Problem 1",
                "instructions": "Choose the correct sentence.",
                "correct_answer_index": 0,
                "target_language_code": "eng",
                "statements": [
                    {
                        "content": "Je parle.",
                        "is_correct": True,
                        "translation": "I speak.",
                    },
                    {
                        "content": "Je parles.",
                        "is_correct": False,
                        "explanation": "Wrong.",
                    },
                ],
                "topic_tags": ["test_data"],
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z",
            },
            {
                "id": "abcdef12-3456-7890-abcd-ef1234567890",
                "problem_type": "grammar",
                "title": "Problem 2",
                "instructions": "Choose the correct sentence.",
                "correct_answer_index": 1,
                "target_language_code": "eng",
                "statements": [
                    {
                        "content": "Tu parle.",
                        "is_correct": False,
                        "explanation": "Wrong.",
                    },
                    {
                        "content": "Tu parles.",
                        "is_correct": True,
                        "translation": "You speak.",
                    },
                ],
                "topic_tags": ["test_data"],
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z",
            },
        ],
    }


@pytest.mark.unit
class TestGetGenerationRequestById:
    """Test get generation request by ID command."""

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_get_by_id_success(
        self,
        mock_get_key,
        mock_request,
        sample_generation_response,
    ):
        """Test successfully getting a generation request by ID."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_generation_response
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "Generation Request Details" in result.output
        assert "87654321" in result.output
        assert "2/2" in result.output  # Progress
        assert "Generated 2 problem(s)" in result.output

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_get_by_id_with_json_output(
        self,
        mock_get_key,
        mock_request,
        sample_generation_response,
    ):
        """Test getting a generation request with JSON output."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_generation_response
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["87654321-4321-8765-4321-876543218765", "--json"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "request_id" in result.output
        assert "entities" in result.output

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_get_by_id_no_problems_yet(
        self,
        mock_get_key,
        mock_request,
    ):
        """Test getting a generation request with no problems generated yet."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "request_id": "87654321-4321-8765-4321-876543218765",
            "status": GenerationStatus.PROCESSING.value,
            "entity_type": EntityType.PROBLEM.value,
            "requested_count": 5,
            "generated_count": 0,
            "failed_count": 0,
            "requested_at": "2023-01-01T12:00:00Z",
            "entities": [],
        }
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "No problems generated yet" in result.output

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_get_by_id_shows_failed_count(
        self,
        mock_get_key,
        mock_request,
    ):
        """Test that failed count is displayed when present."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "request_id": "87654321-4321-8765-4321-876543218765",
            "status": GenerationStatus.PARTIAL.value,
            "entity_type": EntityType.PROBLEM.value,
            "requested_count": 5,
            "generated_count": 3,
            "failed_count": 2,
            "requested_at": "2023-01-01T12:00:00Z",
            "completed_at": "2023-01-01T12:05:00Z",
            "entities": [],
        }
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "Failed: 2" in result.output

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_get_by_id_shows_error_message(
        self,
        mock_get_key,
        mock_request,
    ):
        """Test that error message is displayed when present."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "request_id": "87654321-4321-8765-4321-876543218765",
            "status": GenerationStatus.FAILED.value,
            "entity_type": EntityType.PROBLEM.value,
            "requested_count": 5,
            "generated_count": 0,
            "failed_count": 5,
            "requested_at": "2023-01-01T12:00:00Z",
            "completed_at": "2023-01-01T12:05:00Z",
            "error_message": "LLM rate limit exceeded",
            "entities": [],
        }
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "Error: LLM rate limit exceeded" in result.output


@pytest.mark.unit
class TestGetGenerationRequestErrorHandling:
    """Test error handling for get generation request command."""

    async def test_no_argument_error(self):
        """Test that error is raised when no generation ID is provided."""
        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            [],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code != 0
        assert "Must specify a generation request ID" in result.output

    async def test_no_service_url_error(self):
        """Test that error is raised when service URL not configured."""
        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["87654321-4321-8765-4321-876543218765"],
            obj={},  # No service_url
        )

        assert result.exit_code != 0
        assert "Service URL not configured" in result.output


@pytest.mark.unit
class TestGetGenerationRequestStdinPiping:
    """Test stdin piping for get generation request command."""

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_get_by_id_from_stdin(
        self,
        mock_get_key,
        mock_request,
        sample_generation_response,
    ):
        """Test getting a generation request by ID piped from stdin."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_generation_response
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            [],
            obj={"service_url": "http://localhost:8000"},
            input="87654321-4321-8765-4321-876543218765\n",
        )

        assert result.exit_code == 0
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert (
            "/api/v1/generation-requests/87654321-4321-8765-4321-876543218765"
            in call_kwargs["endpoint"]
        )

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_get_multiple_ids_from_stdin(
        self,
        mock_get_key,
        mock_request,
        sample_generation_response,
    ):
        """Test getting multiple generation requests from stdin."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_generation_response
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            [],
            obj={"service_url": "http://localhost:8000"},
            input="87654321-4321-8765-4321-876543218765\nabcdef12-3456-7890-abcd-ef1234567890\n",
        )

        assert result.exit_code == 0
        # Should call the API twice, once for each ID
        assert mock_request.call_count == 2

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_argument_takes_precedence_over_stdin(
        self,
        mock_get_key,
        mock_request,
        sample_generation_response,
    ):
        """Test that argument takes precedence over stdin."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_generation_response
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
            obj={"service_url": "http://localhost:8000"},
            input="87654321-4321-8765-4321-876543218765\n",
        )

        assert result.exit_code == 0
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        # Should use the argument value, not stdin
        assert (
            "/api/v1/generation-requests/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
            in call_kwargs["endpoint"]
        )

    async def test_json_input_gives_helpful_error(self):
        """Test that JSON input gives a helpful error suggesting jq."""
        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            [],
            obj={"service_url": "http://localhost:8000"},
            input='{"id": "87654321-4321-8765-4321-876543218765"}\n',
        )

        assert result.exit_code != 0
        assert "Input looks like JSON" in result.output
        assert "jq" in result.output

    async def test_invalid_uuid_gives_clear_error(self):
        """Test that invalid UUID input gives a clear error."""
        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            [],
            obj={"service_url": "http://localhost:8000"},
            input="not-a-valid-uuid\n",
        )

        assert result.exit_code != 0
        assert "Invalid UUID" in result.output
        assert "not-a-valid-uuid" in result.output

    @patch("src.cli.generation_requests.commands.make_api_request")
    @patch("src.cli.generation_requests.commands.get_api_key")
    async def test_api_error_handled_gracefully(
        self,
        mock_get_key,
        mock_request,
    ):
        """Test that API errors are handled gracefully."""
        mock_get_key.return_value = "test-api-key"
        mock_request.side_effect = Exception("Connection refused")

        runner = CliRunner()
        result = await runner.invoke(
            get_request,
            ["87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        # Command succeeds but logs error
        assert result.exit_code == 0
        assert "Failed to get generation request" in result.output
        assert "Connection refused" in result.output
