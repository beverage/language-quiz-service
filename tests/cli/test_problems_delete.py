"""Tests for CLI problem delete command."""

from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from asyncclick.testing import CliRunner

from src.cli.problems.delete import delete_problem
from src.schemas.generation_requests import (
    EntityType,
    GenerationRequest,
    GenerationStatus,
)
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
def sample_generation_request():
    """Fixture for a sample GenerationRequest."""
    return GenerationRequest(
        id=UUID("87654321-4321-8765-4321-876543218765"),
        entity_type=EntityType.PROBLEM,
        status=GenerationStatus.COMPLETED,
        requested_count=5,
        generated_count=5,
        failed_count=0,
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        completed_at=datetime(2023, 1, 1, 12, 5, 0, tzinfo=UTC),
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

    async def test_delete_requires_id_or_generation_id(self):
        """Test that delete requires either --id or --generation-id."""
        runner = CliRunner()
        result = await runner.invoke(delete_problem, [])

        assert result.exit_code != 0
        assert "Must specify either --id or --generation-id" in result.output

    async def test_delete_rejects_both_id_and_generation_id(self):
        """Test that delete rejects both --id and --generation-id together."""
        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            [
                "--id",
                "12345678-1234-5678-1234-567812345678",
                "--generation-id",
                "87654321-4321-8765-4321-876543218765",
            ],
        )

        assert result.exit_code != 0
        assert "Cannot specify both --id and --generation-id" in result.output


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
            ["--id", "12345678-1234-5678-1234-567812345678"],
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
            ["--id", "12345678-1234-5678-1234-567812345678"],
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
            ["--id", "12345678-1234-5678-1234-567812345678", "--force"],
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
            ["--id", "12345678-1234-5678-1234-567812345678"],
        )

        assert result.exit_code == 0  # Command doesn't fail, just shows error
        assert "not found" in result.output


@pytest.mark.unit
class TestDeleteProblemByGenerationId:
    """Test delete problems by generation request ID."""

    @patch("src.core.factories.create_generation_request_service")
    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.require_confirmation")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_generation_id_success(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_problem_service,
        mock_create_gen_service,
        sample_generation_request,
        sample_problem,
    ):
        """Test successful deletion by generation request ID."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True

        # Mock generation request service
        mock_gen_service = AsyncMock()
        mock_create_gen_service.return_value = mock_gen_service
        mock_gen_service.get_generation_request_with_entities.return_value = (
            sample_generation_request,
            [sample_problem, sample_problem],  # Two problems
        )

        # Mock problem service
        mock_problem_service = AsyncMock()
        mock_create_problem_service.return_value = mock_problem_service
        mock_problem_service.delete_problems_by_generation_id.return_value = 2

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765"],
        )

        assert result.exit_code == 0
        assert "Deleted 2 problem(s)" in result.output
        mock_problem_service.delete_problems_by_generation_id.assert_called_once()

    @patch("src.core.factories.create_generation_request_service")
    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_generation_id_no_problems(
        self,
        mock_get_remote,
        mock_create_problem_service,
        mock_create_gen_service,
        sample_generation_request,
    ):
        """Test deletion when generation request has no problems."""
        mock_get_remote.return_value = False

        mock_gen_service = AsyncMock()
        mock_create_gen_service.return_value = mock_gen_service
        mock_gen_service.get_generation_request_with_entities.return_value = (
            sample_generation_request,
            [],  # No problems
        )

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765"],
        )

        assert result.exit_code == 0
        assert "No problems to delete" in result.output

    @patch("src.core.factories.create_generation_request_service")
    @patch("src.cli.problems.delete.create_problem_service")
    @patch("src.cli.problems.delete.get_remote_flag")
    async def test_delete_by_generation_id_not_found(
        self,
        mock_get_remote,
        mock_create_problem_service,
        mock_create_gen_service,
    ):
        """Test deletion when generation request is not found."""
        mock_get_remote.return_value = False

        mock_gen_service = AsyncMock()
        mock_create_gen_service.return_value = mock_gen_service
        mock_gen_service.get_generation_request_with_entities.side_effect = Exception(
            "Not found"
        )

        runner = CliRunner()
        result = await runner.invoke(
            delete_problem,
            ["--generation-id", "87654321-4321-8765-4321-876543218765"],
        )

        assert result.exit_code == 0
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
            ["--id", "12345678-1234-5678-1234-567812345678"],
        )

        # Verify confirmation was called with is_remote=True
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("is_remote") is True
