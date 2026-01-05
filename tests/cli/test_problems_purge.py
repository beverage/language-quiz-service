"""Tests for CLI problem purge command."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asyncclick.testing import CliRunner

from src.cli.problems.purge import purge_problems


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

    # Create a chainable mock that supports all filter methods
    def create_chainable_mock(final_result):
        """Create a mock that returns itself for any filter method call."""
        mock = MagicMock()
        mock.execute = AsyncMock(return_value=final_result)
        # Each filter method returns the same mock (chainable)
        mock.contains.return_value = mock
        mock.lte.return_value = mock
        mock.gte.return_value = mock
        mock.neq.return_value = mock
        return mock

    # Setup the query chain for count
    mock_table = MagicMock()
    mock_select = create_chainable_mock(mock_count_result)
    mock_table.select.return_value = mock_select

    # Setup the query chain for delete
    mock_delete = create_chainable_mock(mock_delete_result)
    mock_table.delete.return_value = mock_delete

    mock_client.table.return_value = mock_table

    return mock_client


@pytest.mark.unit
class TestPurgeProblemsBasic:
    """Test basic purge functionality."""

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_all_problems_success(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test successful purge of all problems."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=42)

        runner = CliRunner()
        result = await runner.invoke(purge_problems, [])

        assert result.exit_code == 0
        assert "Deleted 42 problems" in result.output

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_aborted_on_decline(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge aborted when user declines confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = False  # User declines
        mock_get_client.return_value = create_mock_supabase_client(count=10)

        runner = CliRunner()
        result = await runner.invoke(purge_problems, [])

        assert result.exit_code == 0
        assert "Aborted" in result.output

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_force_skips_confirmation(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with --force skips confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=5)

        runner = CliRunner()
        result = await runner.invoke(purge_problems, ["--force"])

        assert result.exit_code == 0
        # Verify confirmation was called with force=True
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("force") is True

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_no_problems_found(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test purge when no problems exist."""
        mock_get_remote.return_value = False
        mock_get_client.return_value = create_mock_supabase_client(count=0)

        runner = CliRunner()
        result = await runner.invoke(purge_problems, [])

        assert result.exit_code == 0
        assert "No problems found" in result.output


@pytest.mark.unit
class TestPurgeProblemsFiltered:
    """Test purge with topic filtering."""

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_topic_filter(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with topic filter."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=15)

        runner = CliRunner()
        result = await runner.invoke(purge_problems, ["--topic", "test_data"])

        assert result.exit_code == 0
        assert "Deleted 15 problems" in result.output
        assert "test_data" in result.output

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_multiple_topics(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with multiple topic filters."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(count=25)

        runner = CliRunner()
        result = await runner.invoke(
            purge_problems, ["--topic", "test_data", "--topic", "cleanup"]
        )

        assert result.exit_code == 0
        assert "Deleted 25 problems" in result.output


@pytest.mark.unit
class TestPurgeProblemsRemoteForbidden:
    """Test that remote purge is forbidden."""

    @patch("src.cli.problems.purge.forbid_remote")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_remote_purge_is_forbidden(
        self,
        mock_get_remote,
        mock_forbid_remote,
    ):
        """Test that remote purge is forbidden."""
        mock_get_remote.return_value = True  # Remote mode
        mock_forbid_remote.return_value = True  # Indicates forbidden

        runner = CliRunner()
        result = await runner.invoke(purge_problems, [])

        # Command should exit early
        assert result.exit_code == 0
        mock_forbid_remote.assert_called_once_with("lqs problem purge", True)

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.forbid_remote")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_local_purge_is_allowed(
        self,
        mock_get_remote,
        mock_forbid_remote,
        mock_get_client,
    ):
        """Test that local purge is allowed."""
        mock_get_remote.return_value = False  # Local mode
        mock_forbid_remote.return_value = False  # Not forbidden
        mock_get_client.return_value = create_mock_supabase_client(count=0)

        runner = CliRunner()
        result = await runner.invoke(purge_problems, [])

        assert result.exit_code == 0
        mock_forbid_remote.assert_called_once_with("lqs problem purge", False)


@pytest.mark.unit
class TestPurgeProblemsErrorHandling:
    """Test error handling for purge command."""

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_handles_database_error(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test that purge handles database errors gracefully."""
        mock_get_remote.return_value = False
        mock_get_client.side_effect = Exception("Database connection failed")

        runner = CliRunner()
        result = await runner.invoke(purge_problems, [])

        assert result.exit_code == 0  # Command doesn't crash
        assert "Error" in result.output


@pytest.mark.unit
class TestPurgeProblemsDateFilters:
    """Test purge with date filters."""

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_older_than_duration(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with --older-than using duration string."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_client = create_mock_supabase_client(count=20)
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = await runner.invoke(purge_problems, ["--older-than", "7d", "--force"])

        assert result.exit_code == 0
        assert "Deleted 20 problems" in result.output
        assert "created before" in result.output

        # Verify lte was called on the query chain
        mock_table = mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_select.lte.assert_called()

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_newer_than_duration(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with --newer-than using duration string."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_client = create_mock_supabase_client(count=10)
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = await runner.invoke(purge_problems, ["--newer-than", "1d", "--force"])

        assert result.exit_code == 0
        assert "Deleted 10 problems" in result.output
        assert "created after" in result.output

        # Verify gte was called on the query chain
        mock_table = mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_select.gte.assert_called()

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_date_range(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with both --older-than and --newer-than for date range."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_client = create_mock_supabase_client(count=5)
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = await runner.invoke(
            purge_problems, ["--newer-than", "7d", "--older-than", "1d", "--force"]
        )

        assert result.exit_code == 0
        assert "Deleted 5 problems" in result.output
        assert "created before" in result.output
        assert "created after" in result.output

        # Verify both lte and gte were called
        mock_table = mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_select.lte.assert_called()
        mock_select.gte.assert_called()

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_older_than_and_topic(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge combining --older-than with --topic filters."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_client = create_mock_supabase_client(count=8)
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = await runner.invoke(
            purge_problems,
            ["--older-than", "2d", "--topic", "test_data", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted 8 problems" in result.output
        assert "created before" in result.output
        assert "test_data" in result.output

        # Verify both contains (topic) and lte (date) were called
        mock_table = mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_select.contains.assert_called()
        mock_select.lte.assert_called()

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_older_than_no_matches(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test purge with --older-than when no problems match."""
        mock_get_remote.return_value = False
        mock_get_client.return_value = create_mock_supabase_client(count=0)

        runner = CliRunner()
        result = await runner.invoke(purge_problems, ["--older-than", "30d"])

        assert result.exit_code == 0
        assert "No problems found" in result.output

    @patch("src.cli.problems.purge.get_supabase_client")
    @patch("src.cli.problems.purge.require_confirmation")
    @patch("src.cli.problems.purge.get_remote_flag")
    async def test_purge_with_absolute_date(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with --older-than using absolute date."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_client = create_mock_supabase_client(count=15)
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = await runner.invoke(
            purge_problems, ["--older-than", "2025-01-01", "--force"]
        )

        assert result.exit_code == 0
        assert "Deleted 15 problems" in result.output
        assert "created before" in result.output
