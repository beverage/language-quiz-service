"""Tests for CLI generation request commands."""

from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from asyncclick.testing import CliRunner

from src.cli.generation_requests.commands import (
    clean_requests,
    get_status,
    list_requests,
)
from src.schemas.generation_requests import (
    EntityType,
    GenerationRequest,
    GenerationStatus,
)


@pytest.fixture
def sample_generation_request():
    """Sample generation request."""
    return GenerationRequest(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        entity_type=EntityType.PROBLEM,
        status=GenerationStatus.COMPLETED,
        requested_count=10,
        generated_count=10,
        failed_count=0,
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        started_at=datetime(2023, 1, 1, 12, 0, 5, tzinfo=UTC),
        completed_at=datetime(2023, 1, 1, 12, 1, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_pending_request():
    """Sample pending generation request."""
    return GenerationRequest(
        id=UUID("87654321-4321-8765-4321-876543218765"),
        entity_type=EntityType.PROBLEM,
        status=GenerationStatus.PENDING,
        requested_count=5,
        generated_count=0,
        failed_count=0,
        requested_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_failed_request():
    """Sample failed generation request."""
    return GenerationRequest(
        id=UUID("abcdef12-3456-7890-abcd-ef1234567890"),
        entity_type=EntityType.PROBLEM,
        status=GenerationStatus.FAILED,
        requested_count=5,
        generated_count=2,
        failed_count=3,
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        error_message="OpenAI API rate limit exceeded",
    )


@pytest.mark.unit
class TestListRequests:
    """Test list generation requests command."""

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_list_shows_requests(
        self,
        mock_create_repo,
        sample_generation_request,
        sample_pending_request,
    ):
        """Test that list shows generation requests."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = (
            [sample_generation_request, sample_pending_request],
            2,
        )

        runner = CliRunner()
        result = await runner.invoke(list_requests, [])

        assert result.exit_code == 0
        assert "showing 2 of 2" in result.output
        assert "12345678" in result.output  # Request ID
        assert "completed" in result.output
        assert "pending" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_list_with_status_filter(
        self,
        mock_create_repo,
        sample_generation_request,
    ):
        """Test list with status filter."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([sample_generation_request], 1)

        runner = CliRunner()
        result = await runner.invoke(list_requests, ["--status", "completed"])

        assert result.exit_code == 0
        mock_repo.get_all_requests.assert_called_once()
        call_kwargs = mock_repo.get_all_requests.call_args.kwargs
        assert call_kwargs["status"] == GenerationStatus.COMPLETED

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_list_empty_results(self, mock_create_repo):
        """Test list with no results."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([], 0)

        runner = CliRunner()
        result = await runner.invoke(list_requests, [])

        assert result.exit_code == 0
        assert "No generation requests found" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_list_shows_failed_errors(
        self,
        mock_create_repo,
        sample_failed_request,
    ):
        """Test that failed requests show error message."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([sample_failed_request], 1)

        runner = CliRunner()
        result = await runner.invoke(list_requests, [])

        assert result.exit_code == 0
        assert "failed" in result.output
        assert "Error:" in result.output or "rate limit" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_list_handles_database_error(self, mock_create_repo):
        """Test list handles database errors gracefully."""
        mock_create_repo.side_effect = Exception("Database error")

        runner = CliRunner()
        result = await runner.invoke(list_requests, [])

        assert result.exit_code == 0
        assert "Error" in result.output


@pytest.mark.unit
class TestGetStatus:
    """Test get status command."""

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_get_status_shows_details(
        self,
        mock_create_repo,
        sample_generation_request,
    ):
        """Test that status shows request details."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_generation_request.return_value = sample_generation_request
        mock_repo.get_problems_by_request_id.return_value = []

        runner = CliRunner()
        result = await runner.invoke(
            get_status, ["12345678-1234-5678-1234-567812345678"]
        )

        assert result.exit_code == 0
        assert "12345678" in result.output
        assert "completed" in result.output
        assert "10/10" in result.output  # Progress
        assert "Duration" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_get_status_not_found(self, mock_create_repo):
        """Test status with non-existent request."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_generation_request.return_value = None

        runner = CliRunner()
        result = await runner.invoke(
            get_status, ["12345678-1234-5678-1234-567812345678"]
        )

        assert result.exit_code == 0
        assert "not found" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_get_status_shows_problems(
        self,
        mock_create_repo,
        sample_generation_request,
    ):
        """Test that status shows associated problems."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_generation_request.return_value = sample_generation_request
        mock_repo.get_problems_by_request_id.return_value = [
            {"id": "prob-1", "title": "Problem 1"},
            {"id": "prob-2", "title": "Problem 2"},
        ]

        runner = CliRunner()
        result = await runner.invoke(
            get_status, ["12345678-1234-5678-1234-567812345678"]
        )

        assert result.exit_code == 0
        assert "Problems Generated: 2" in result.output
        assert "prob-1" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    async def test_get_status_shows_error_message(
        self,
        mock_create_repo,
        sample_failed_request,
    ):
        """Test that status shows error message for failed requests."""
        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_generation_request.return_value = sample_failed_request
        mock_repo.get_problems_by_request_id.return_value = []

        runner = CliRunner()
        result = await runner.invoke(
            get_status, ["abcdef12-3456-7890-abcd-ef1234567890"]
        )

        assert result.exit_code == 0
        assert "rate limit" in result.output


@pytest.mark.unit
class TestCleanRequests:
    """Test clean generation requests command."""

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    @patch("src.cli.generation_requests.commands.require_confirmation")
    @patch("src.cli.generation_requests.commands.get_remote_flag")
    async def test_clean_deletes_old_requests(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_repo,
    ):
        """Test cleaning old requests."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True

        # Create an old completed request
        old_request = GenerationRequest(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            entity_type=EntityType.PROBLEM,
            status=GenerationStatus.COMPLETED,
            requested_count=5,
            generated_count=5,
            failed_count=0,
            requested_at=datetime.now(UTC) - timedelta(days=30),
        )

        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([old_request], 1)
        mock_repo.delete_old_requests.return_value = 1

        runner = CliRunner()
        result = await runner.invoke(clean_requests, ["--older-than", "7d"])

        assert result.exit_code == 0
        assert "Found 1 completed/failed/expired requests" in result.output
        assert "Deleted 1 generation requests" in result.output
        mock_repo.delete_old_requests.assert_called_once()
        # Verify it was called with a timedelta
        call_args = mock_repo.delete_old_requests.call_args
        assert call_args is not None
        assert "older_than" in call_args.kwargs
        assert isinstance(call_args.kwargs["older_than"], timedelta)
        assert call_args.kwargs["older_than"] == timedelta(days=7)
        # Verify metadata_contains is None when no topic filter
        assert call_args.kwargs.get("metadata_contains") is None

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    @patch("src.cli.generation_requests.commands.get_remote_flag")
    async def test_clean_no_old_requests(
        self,
        mock_get_remote,
        mock_create_repo,
    ):
        """Test clean when no old requests exist."""
        mock_get_remote.return_value = False

        # Create a recent completed request (not old enough to delete)
        recent_request = GenerationRequest(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            entity_type=EntityType.PROBLEM,
            status=GenerationStatus.COMPLETED,
            requested_count=5,
            generated_count=5,
            failed_count=0,
            requested_at=datetime.now(UTC) - timedelta(days=1),  # Only 1 day old
        )

        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([recent_request], 1)

        runner = CliRunner()
        result = await runner.invoke(clean_requests, ["--older-than", "7d"])

        assert result.exit_code == 0
        assert "No completed/failed/expired requests older than 7d" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    @patch("src.cli.generation_requests.commands.require_confirmation")
    @patch("src.cli.generation_requests.commands.get_remote_flag")
    async def test_clean_aborted_on_decline(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_repo,
    ):
        """Test clean aborted when user declines confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = False

        old_request = GenerationRequest(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            entity_type=EntityType.PROBLEM,
            status=GenerationStatus.COMPLETED,
            requested_count=5,
            generated_count=5,
            failed_count=0,
            requested_at=datetime.now(UTC) - timedelta(days=30),
        )

        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([old_request], 1)

        runner = CliRunner()
        result = await runner.invoke(clean_requests, [])

        assert result.exit_code == 0
        assert "Aborted" in result.output

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    @patch("src.cli.generation_requests.commands.require_confirmation")
    @patch("src.cli.generation_requests.commands.get_remote_flag")
    async def test_clean_with_force(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_repo,
    ):
        """Test clean with --force skips confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True

        old_request = GenerationRequest(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            entity_type=EntityType.PROBLEM,
            status=GenerationStatus.COMPLETED,
            requested_count=5,
            generated_count=5,
            failed_count=0,
            requested_at=datetime.now(UTC) - timedelta(days=30),
        )

        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([old_request], 1)
        mock_repo.delete_old_requests.return_value = 1

        runner = CliRunner()
        result = await runner.invoke(clean_requests, ["--force"])

        assert result.exit_code == 0
        # Verify confirmation was called with force=True
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("force") is True

    @patch("src.cli.generation_requests.commands.create_generation_request_repository")
    @patch("src.cli.generation_requests.commands.require_confirmation")
    @patch("src.cli.generation_requests.commands.get_remote_flag")
    async def test_clean_with_topic_filter(
        self,
        mock_get_remote,
        mock_confirm,
        mock_create_repo,
    ):
        """Test clean with --topic filter uses metadata filtering."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True

        # Create an old completed request with test_data tag
        old_request = GenerationRequest(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            entity_type=EntityType.PROBLEM,
            status=GenerationStatus.COMPLETED,
            requested_count=5,
            generated_count=5,
            failed_count=0,
            requested_at=datetime.now(UTC) - timedelta(days=30),
            metadata={"topic_tags": ["test_data"]},
        )

        mock_repo = AsyncMock()
        mock_create_repo.return_value = mock_repo
        mock_repo.get_all_requests.return_value = ([old_request], 1)
        mock_repo.delete_old_requests.return_value = 1

        runner = CliRunner()
        result = await runner.invoke(
            clean_requests, ["--older-than", "7d", "--topic", "test_data"]
        )

        assert result.exit_code == 0
        assert "Found 1 completed/failed/expired requests" in result.output
        mock_repo.delete_old_requests.assert_called_once()
        # Verify metadata_contains was passed
        call_args = mock_repo.delete_old_requests.call_args
        assert call_args is not None
        assert "metadata_contains" in call_args.kwargs
        assert call_args.kwargs["metadata_contains"] == {"topic_tags": ["test_data"]}
