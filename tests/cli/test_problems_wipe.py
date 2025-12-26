"""Tests for CLI problem wipe command."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asyncclick.testing import CliRunner

from src.cli.problems.wipe import wipe_problems


def create_mock_supabase_client(count: int = 0, delete_count: int | None = None):
    """Create a properly configured mock Supabase client.

    Args:
        count: Number of problems to return in count query
        delete_count: Number of problems deleted (defaults to count)
    """
    if delete_count is None:
        delete_count = count

    mock_client = MagicMock()

    # Mock count result
    mock_count_result = MagicMock()
    mock_count_result.count = count
    mock_count_result.data = [{"id": str(i)} for i in range(count)]

    # Mock delete result
    mock_delete_result = MagicMock()
    mock_delete_result.data = [{"id": str(i)} for i in range(delete_count)]

    # Setup the query chain for count (no filter)
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_select.execute = AsyncMock(return_value=mock_count_result)
    mock_table.select.return_value = mock_select

    # Setup the query chain for count with filter
    mock_select_filtered = MagicMock()
    mock_select_filtered.execute = AsyncMock(return_value=mock_count_result)
    mock_select.contains.return_value = mock_select_filtered

    # Setup the query chain for delete (no filter)
    mock_delete = MagicMock()
    mock_delete_neq = MagicMock()
    mock_delete_neq.execute = AsyncMock(return_value=mock_delete_result)
    mock_delete.neq.return_value = mock_delete_neq
    mock_table.delete.return_value = mock_delete

    # Setup delete with filter
    mock_delete_filtered = MagicMock()
    mock_delete_filtered.execute = AsyncMock(return_value=mock_delete_result)
    mock_delete.contains.return_value = mock_delete_filtered

    mock_client.table.return_value = mock_table

    return mock_client


@pytest.mark.unit
class TestWipeProblemsBasic:
    """Test basic wipe functionality."""

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.require_confirmation")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_wipe_all_problems_success(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test successful wipe of all problems."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=42)

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, [])

        assert result.exit_code == 0
        assert "Deleted 42 problems" in result.output

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.require_confirmation")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_wipe_aborted_on_decline(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test wipe aborted when user declines confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = False  # User declines
        mock_get_client.return_value = create_mock_supabase_client(count=10)

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, [])

        assert result.exit_code == 0
        assert "Aborted" in result.output

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.require_confirmation")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_wipe_with_force_skips_confirmation(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test wipe with --force skips confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=5)

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, ["--force"])

        assert result.exit_code == 0
        # Verify confirmation was called with force=True
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("force") is True

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_wipe_no_problems_found(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test wipe when no problems exist."""
        mock_get_remote.return_value = False
        mock_get_client.return_value = create_mock_supabase_client(count=0)

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, [])

        assert result.exit_code == 0
        assert "No problems found" in result.output


@pytest.mark.unit
class TestWipeProblemsFiltered:
    """Test wipe with topic filtering."""

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.require_confirmation")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_wipe_with_topic_filter(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test wipe with topic filter."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=15)

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, ["--topic", "test_data"])

        assert result.exit_code == 0
        assert "Deleted 15 problems" in result.output
        assert "test_data" in result.output

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.require_confirmation")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_wipe_with_multiple_topics(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test wipe with multiple topic filters."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=25)

        runner = CliRunner()
        result = await runner.invoke(
            wipe_problems, ["--topic", "test_data", "--topic", "cleanup"]
        )

        assert result.exit_code == 0
        assert "Deleted 25 problems" in result.output


@pytest.mark.unit
class TestWipeProblemsRemoteForbidden:
    """Test that remote wipe is forbidden."""

    @patch("src.cli.problems.wipe.forbid_remote")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_remote_wipe_is_forbidden(
        self,
        mock_get_remote,
        mock_forbid_remote,
    ):
        """Test that remote wipe is forbidden."""
        mock_get_remote.return_value = True  # Remote mode
        mock_forbid_remote.return_value = True  # Indicates forbidden

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, [])

        # Command should exit early
        assert result.exit_code == 0
        mock_forbid_remote.assert_called_once_with("lqs problem wipe", True)

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.forbid_remote")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_local_wipe_is_allowed(
        self,
        mock_get_remote,
        mock_forbid_remote,
        mock_get_client,
    ):
        """Test that local wipe is allowed."""
        mock_get_remote.return_value = False  # Local mode
        mock_forbid_remote.return_value = False  # Not forbidden
        mock_get_client.return_value = create_mock_supabase_client(count=0)

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, [])

        assert result.exit_code == 0
        mock_forbid_remote.assert_called_once_with("lqs problem wipe", False)


@pytest.mark.unit
class TestWipeProblemsErrorHandling:
    """Test error handling for wipe command."""

    @patch("src.cli.problems.wipe.get_supabase_client")
    @patch("src.cli.problems.wipe.get_remote_flag")
    async def test_wipe_handles_database_error(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test that wipe handles database errors gracefully."""
        mock_get_remote.return_value = False
        mock_get_client.side_effect = Exception("Database connection failed")

        runner = CliRunner()
        result = await runner.invoke(wipe_problems, [])

        assert result.exit_code == 0  # Command doesn't crash
        assert "Error" in result.output
