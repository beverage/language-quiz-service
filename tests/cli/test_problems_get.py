"""Tests for CLI problems get command."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from asyncclick.testing import CliRunner

from src.cli.problems.get import get_problem
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
            ["12345678-1234-5678-1234-567812345678"],
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
            ["12345678-1234-5678-1234-567812345678", "--json"],
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
            ["12345678-1234-5678-1234-567812345678", "--verbose"],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code == 0
        # Check that include_metadata=true was passed
        call_kwargs = mock_request.call_args.kwargs
        assert "include_metadata=true" in call_kwargs["endpoint"]


@pytest.mark.unit
class TestGetProblemErrorHandling:
    """Test error handling for get problem command."""

    async def test_no_argument_error(self):
        """Test that error is raised when no problem ID is provided."""
        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            [],
            obj={"service_url": "http://localhost:8000"},
        )

        assert result.exit_code != 0
        assert "Must specify a problem ID" in result.output


@pytest.mark.unit
class TestGetProblemStdinPiping:
    """Test stdin piping for get problem command."""

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_by_id_from_stdin(
        self,
        mock_get_key,
        mock_request,
        sample_problem,
    ):
        """Test getting a problem by ID piped from stdin."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_problem.model_dump(mode="json")
        mock_request.return_value = mock_response

        runner = CliRunner()
        # Pipe the ID via stdin
        result = await runner.invoke(
            get_problem,
            [],
            obj={"service_url": "http://localhost:8000"},
            input="12345678-1234-5678-1234-567812345678\n",
        )

        assert result.exit_code == 0
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        assert (
            "/api/v1/problems/12345678-1234-5678-1234-567812345678"
            in call_kwargs["endpoint"]
        )

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_get_multiple_ids_from_stdin(
        self,
        mock_get_key,
        mock_request,
        sample_problem,
    ):
        """Test getting multiple problems when multiple IDs are piped."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_problem.model_dump(mode="json")
        mock_request.return_value = mock_response

        runner = CliRunner()
        # Pipe multiple IDs - all should be processed
        result = await runner.invoke(
            get_problem,
            [],
            obj={"service_url": "http://localhost:8000"},
            input="12345678-1234-5678-1234-567812345678\nabcdef12-3456-7890-abcd-ef1234567890\n",
        )

        assert result.exit_code == 0
        # Should call the API twice, once for each ID
        assert mock_request.call_count == 2

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_option_takes_precedence_over_stdin(
        self,
        mock_get_key,
        mock_request,
        sample_problem,
    ):
        """Test that --id option takes precedence over stdin."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.json.return_value = sample_problem.model_dump(mode="json")
        mock_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
            obj={"service_url": "http://localhost:8000"},
            input="12345678-1234-5678-1234-567812345678\n",
        )

        assert result.exit_code == 0
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        # Should use the option value, not stdin
        assert (
            "/api/v1/problems/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
            in call_kwargs["endpoint"]
        )

    async def test_json_input_gives_helpful_error(self):
        """Test that JSON input gives a helpful error suggesting jq."""
        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            [],
            obj={"service_url": "http://localhost:8000"},
            input='{"problems": [{"id": "12345678-1234-5678-1234-567812345678"}]}\n',
        )

        assert result.exit_code != 0
        assert "Input looks like JSON" in result.output
        assert "jq" in result.output

    async def test_invalid_uuid_gives_clear_error(self):
        """Test that invalid UUID input gives a clear error."""
        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            [],
            obj={"service_url": "http://localhost:8000"},
            input="not-a-valid-uuid\n",
        )

        assert result.exit_code != 0
        assert "Invalid UUID" in result.output
        assert "not-a-valid-uuid" in result.output

    @patch("src.cli.problems.get.make_api_request")
    @patch("src.cli.problems.get.get_api_key")
    async def test_api_error_handled_gracefully(
        self,
        mock_get_key,
        mock_request,
    ):
        """Test that API errors are handled gracefully (logged, command continues)."""
        mock_get_key.return_value = "test-api-key"
        mock_request.side_effect = Exception("Connection refused")

        runner = CliRunner()
        result = await runner.invoke(
            get_problem,
            ["12345678-1234-5678-1234-567812345678"],
            obj={"service_url": "http://localhost:8000"},
        )

        # Command succeeds even if individual IDs fail (graceful handling)
        assert result.exit_code == 0
        # Error is logged (stderr is mixed with stdout in asyncclick)
        assert "Failed to get problem" in result.output
        assert "Connection refused" in result.output

    async def test_no_service_url_error(self):
        """Test that error is raised when service URL not configured."""
        runner = CliRunner()
        # Pass empty obj dict (no service_url)
        result = await runner.invoke(
            get_problem,
            ["12345678-1234-5678-1234-567812345678"],
            obj={},
        )

        assert result.exit_code != 0
        assert "Service URL not configured" in result.output
