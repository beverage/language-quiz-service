"""Tests for CLI problem delete command."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from asyncclick.testing import CliRunner

from src.cli.problems.delete import delete_problem
from src.schemas.problems import Problem, ProblemType


@pytest.fixture
def sample_problem():
    """Fixture for a sample Problem."""
    return Problem(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        problem_type=ProblemType.GRAMMAR,
        title="Test Grammar Problem",
        instructions="Choose the correct verb form",
        correct_answer_index=0,
        target_language_code="eng",
        statements=[
            {
                "content": "J'ai un livre.",
                "is_correct": True,
                "translation": "I have a book.",
            },
            {
                "content": "Je ai un livre.",
                "is_correct": False,
                "explanation": "Missing contraction",
            },
        ],
        topic_tags=["test"],
        source_statement_ids=[],
        metadata={},
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def mock_cli_context():
    """Create a mock CLI context with remote=False."""
    mock_root = MagicMock()
    mock_root.obj = {"remote": False, "service_url": "http://localhost:8000"}
    mock_root.params = {"detailed": False}
    return mock_root


@pytest.mark.unit
class TestDeleteProblemValidation:
    """Test validation for delete command options."""

    async def test_delete_requires_problem_id(self):
        """Test that delete requires a problem ID."""
        runner = CliRunner()
        result = await runner.invoke(delete_problem, [])

        assert result.exit_code != 0
        assert "Must specify a problem ID" in result.output


@pytest.mark.unit
class TestDeleteProblemById:
    """Test delete problem by ID."""

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.require_confirmation")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_id_success(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_service,
        sample_problem,
    ):
        """Test successful deletion by problem ID."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.return_value = sample_problem
        mock_service.delete_problem.return_value = True

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["12345678-1234-5678-1234-567812345678"],
        )

        assert result.exit_code == 0
        assert "deleted successfully" in result.output
        mock_service.delete_problem.assert_called_once()

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.require_confirmation")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_id_aborted(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_service,
        sample_problem,
    ):
        """Test deletion aborted when user declines confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = False  # User declines

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.return_value = sample_problem

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["12345678-1234-5678-1234-567812345678"],
        )

        assert result.exit_code == 0
        assert "Aborted" in result.output

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.require_confirmation")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_id_with_force(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_service,
        sample_problem,
    ):
        """Test deletion with --force skips confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True  # Should be called with force=True

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.return_value = sample_problem
        mock_service.delete_problem.return_value = True

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["12345678-1234-5678-1234-567812345678", "--force"],
        )

        assert result.exit_code == 0
        # Verify confirmation was called with force=True
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("force") is True

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_id_not_found(
        self,
        mock_get_remote,
        mock_create_service,
    ):
        """Test deletion when problem is not found."""
        mock_get_remote.return_value = False

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.side_effect = Exception("Problem not found")

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["12345678-1234-5678-1234-567812345678"],
        )

        assert result.exit_code == 0  # Command doesn't fail, just shows error
        assert "not found" in result.output


@pytest.mark.unit
class TestDeleteProblemRemoteConfirmation:
    """Test remote confirmation behavior for delete command."""

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.require_confirmation")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_remote_delete_calls_confirmation_with_remote_flag(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_service,
        sample_problem,
    ):
        """Test that remote delete passes is_remote=True to confirmation."""
        mock_get_remote.return_value = True  # Remote mode
        mock_confirm.return_value = True

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.return_value = sample_problem
        mock_service.delete_problem.return_value = True

        runner = CliRunner()
        await runner.invoke(
            delete_problem,
            ["12345678-1234-5678-1234-567812345678"],
        )

        # Verify confirmation was called with is_remote=True
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("is_remote") is True


@pytest.mark.unit
class TestDeleteProblemStdinPiping:
    """Test stdin piping for delete problem command."""

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.require_confirmation")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_id_from_stdin(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_service,
        sample_problem,
    ):
        """Test deleting a problem by ID piped from stdin."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.return_value = sample_problem
        mock_service.delete_problem.return_value = True

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["--force"],
            input="12345678-1234-5678-1234-567812345678\n",
        )

        assert result.exit_code == 0
        assert "deleted successfully" in result.output
        mock_service.delete_problem.assert_called_once_with(
            UUID("12345678-1234-5678-1234-567812345678")
        )

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_multiple_ids_requires_force(
        self,
        mock_get_remote,
        mock_create_service,
    ):
        """Test that multiple IDs require --force flag."""
        mock_get_remote.return_value = False

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            [],  # No --force
            input="12345678-1234-5678-1234-567812345678\nabcdef12-3456-7890-abcd-ef1234567890\n",
        )

        assert result.exit_code != 0
        assert "Multiple IDs detected" in result.output
        assert "--force" in result.output

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_multiple_ids_with_force(
        self,
        mock_get_remote,
        mock_create_service,
        sample_problem,
    ):
        """Test deleting multiple problems with --force."""
        mock_get_remote.return_value = False

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.return_value = sample_problem
        mock_service.delete_problem.return_value = True

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["--force"],
            input="12345678-1234-5678-1234-567812345678\nabcdef12-3456-7890-abcd-ef1234567890\n",
        )

        assert result.exit_code == 0
        assert mock_service.delete_problem.call_count == 2
        assert "Deleted 2 problem(s)" in result.output

    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.require_confirmation")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_option_takes_precedence_over_stdin(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_service,
        sample_problem,
    ):
        """Test that --id option takes precedence over stdin."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True

        mock_service = AsyncMock()
        mock_create_service.return_value = mock_service
        mock_service.get_problem_by_id.return_value = sample_problem
        mock_service.delete_problem.return_value = True

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "--force"],
            input="12345678-1234-5678-1234-567812345678\n",
        )

        assert result.exit_code == 0
        # Should use the option value, not stdin
        mock_service.delete_problem.assert_called_once_with(
            UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        )

    async def test_delete_invalid_uuid_from_stdin(self):
        """Test that invalid UUID from stdin raises proper error."""
        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["--force"],
            input="not-a-valid-uuid\n",
        )

        assert result.exit_code != 0
        assert "Invalid UUID" in result.output

    async def test_delete_json_input_gives_helpful_error(self):
        """Test that JSON input gives a helpful error suggesting jq."""
        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["--force"],
            input='{"problems": [{"id": "12345678-1234-5678-1234-567812345678"}]}\n',
        )

        assert result.exit_code != 0
        assert "Input looks like JSON" in result.output
        assert "jq" in result.output
