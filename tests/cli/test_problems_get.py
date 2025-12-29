"""Tests for CLI problems get command."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from asyncclick.testing import CliRunner

from src.cli.problems.get import get_problem
from src.schemas.generation_requests import EntityType, GenerationStatus
from src.schemas.problems import Problem, ProblemType


@pytest.fixture
def sample_problem():
    """Sample problem for testing."""
    return Problem(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        problem_type=ProblemType.GRAMMAR,
        title="Test Grammar Problem",
        instructions="Choose the correct sentence.",
        correct_answer_index=0,
        target_language_code="eng",
        statements=[
            {
                "content": "Je parle français.",
                "is_correct": True,
                "translation": "I speak French.",
            },
            {
                "content": "Je parles français.",
                "is_correct": False,
                "explanation": "Incorrect conjugation - 'parles' is used with 'tu'.",
            },
        ],
        topic_tags=["test_data"],
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


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


@pytest.fixture
def mock_context():
    """Create a mock click context with service_url."""
    ctx = MagicMock()
    ctx.find_root.return_value.obj = {"service_url": "http://localhost:8000"}
    ctx.find_root.return_value.params = {"detailed": False}
    return ctx


@pytest.mark.unit
class TestGetProblemById:
    """Test get problem by ID command."""

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_id_success(
        self,
        mock_get_key,
        mock_request,
        sample_problem,
    ):
        """Test successfully getting a problem by ID."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_problem.model_dump(mode="json")
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["--id", "12345678-1234-5678-1234-567812345678"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "Test Grammar Problem" in result.output or "Je parle" in result.output
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert (
            "/api/v1/problems/12345678-1234-5678-1234-567812345678"
            in call_kwargs["endpoint"]
        )

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_id_with_json_output(
        self,
        mock_get_key,
        mock_request,
        sample_problem,
    ):
        """Test getting problem by ID with JSON output."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_problem.model_dump(mode="json")
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["--id", "12345678-1234-5678-1234-567812345678", "--json"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        # JSON output should contain the raw data
        assert "12345678-1234-5678-1234-567812345678" in result.output
        assert "problem_type" in result.output

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_id_with_verbose(
        self,
        mock_get_key,
        mock_request,
        sample_problem,
    ):
        """Test getting problem by ID with verbose flag passes include_metadata."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_problem.model_dump(mode="json")
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["--id", "12345678-1234-5678-1234-567812345678", "--verbose"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        # Check that include_metadata=true was passed
        call_kwargs = mock_request.call_args.kwargs
        assert "include_metadata=true" in call_kwargs["endpoint"]


@pytest.mark.unit
class TestGetProblemsByGenerationId:
    """Test get problems by generation ID command."""

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_generation_id_success(
        self,
        mock_get_key,
        mock_request,
        sample_generation_response,
    ):
        """Test successfully getting problems by generation ID."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_generation_response
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "Generation Request Details" in result.output
        assert "87654321" in result.output
        assert "2/2" in result.output  # Progress
        assert "Generated 2 problem(s)" in result.output

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_generation_id_with_json_output(
        self,
        mock_get_key,
        mock_request,
        sample_generation_response,
    ):
        """Test getting problems by generation ID with JSON output."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_generation_response
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765", "--json"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "request_id" in result.output
        assert "entities" in result.output

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_generation_id_no_problems(
        self,
        mock_get_key,
        mock_request,
    ):
        """Test getting problems by generation ID when no problems yet."""
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
            get_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "No problems generated yet" in result.output

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_generation_id_shows_failed_count(
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
            get_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "Failed: 2" in result.output

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_generation_id_shows_error_message(
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
            get_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        assert "Error: LLM rate limit exceeded" in result.output


@pytest.mark.unit
class TestGetProblemErrorHandling:
    """Test error handling for get problem command."""

    async def test_no_options_error(self):
        """Test that error is raised when no options are provided."""
        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            [],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code != 0
        assert "Must specify either --id or --generation-id" in result.output

    async def test_both_options_error(self):
        """Test that error is raised when both options are provided."""
        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            [
                "--id",
                "12345678-1234-5678-1234-567812345678",
                "--generation-id",
                "87654321-4321-8765-4321-876543218765",
            ],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code != 0
        assert "Cannot specify both --id and --generation-id" in result.output

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_api_error_handled(
        self,
        mock_get_key,
        mock_request,
    ):
        """Test that API errors are handled gracefully."""
        mock_get_key.return_value = "test-api-key"
        mock_request.side_effect = Exception("Connection refused")

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["--id", "12345678-1234-5678-1234-567812345678"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code != 0
        assert "Failed to get problem(s)" in result.output
        assert "Connection refused" in result.output

    async def test_no_service_url_error(self):
        """Test that error is raised when service URL not configured."""
        runner = CliRunner()
        # Pass empty obj dict (no service_url)
        result = await runner.invoke(
            get_problem,
            ["--id", "12345678-1234-5678-1234-567812345678"],
            obj={},
        )

        assert result.exit_code != 0
        assert "Service URL not configured" in result.output
