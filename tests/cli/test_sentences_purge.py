"""Tests for CLI sentence purge command."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from asyncclick.testing import CliRunner

from src.cli.sentences.purge import purge_orphaned_sentences


def create_mock_supabase_client(
    sentence_count: int = 0,
    problem_count: int = 0,
    orphaned_count: int = 0,
    delete_count: int | None = None,
):
    """Create a properly configured mock Supabase client.

    Args:
        sentence_count: Number of sentences to return
        problem_count: Number of problems to return
        orphaned_count: Number of orphaned sentences (not in any problem)
        delete_count: Number of sentences deleted (defaults to orphaned_count)
    """
    if delete_count is None:
        delete_count = orphaned_count

    mock_client = MagicMock()

    # Create sentence IDs
    all_sentence_ids = [uuid4() for _ in range(sentence_count)]
    # Create problem with source_statement_ids (referenced sentences)
    referenced_ids = set(all_sentence_ids[: sentence_count - orphaned_count])
    orphaned_ids = set(all_sentence_ids[sentence_count - orphaned_count :])

    # Mock sentences result
    mock_sentences_result = MagicMock()
    mock_sentences_result.data = [{"id": str(sid)} for sid in all_sentence_ids]

    # Mock problems result
    mock_problems_result = MagicMock()
    if problem_count > 0 and referenced_ids:
        # Create problems that reference some sentences
        problems_data = []
        referenced_list = list(referenced_ids)
        # Distribute referenced sentences across problems
        for i in range(problem_count):
            start_idx = i * len(referenced_list) // problem_count
            end_idx = (i + 1) * len(referenced_list) // problem_count
            problems_data.append(
                {
                    "source_statement_ids": [
                        str(rid) for rid in referenced_list[start_idx:end_idx]
                    ]
                }
            )
        mock_problems_result.data = problems_data
    else:
        mock_problems_result.data = []

    # Mock delete result
    mock_delete_result = MagicMock()
    mock_delete_result.data = [
        {"id": str(sid)} for sid in list(orphaned_ids)[:delete_count]
    ]

    # Setup sentences query
    mock_sentences_table = MagicMock()
    mock_sentences_select = MagicMock()
    mock_sentences_select.execute = AsyncMock(return_value=mock_sentences_result)
    mock_sentences_table.select.return_value = mock_sentences_select

    # Setup problems query
    mock_problems_table = MagicMock()
    mock_problems_select = MagicMock()
    mock_problems_select.execute = AsyncMock(return_value=mock_problems_result)
    mock_problems_table.select.return_value = mock_problems_select

    # Setup delete query (on sentences table)
    mock_delete_query = MagicMock()
    mock_delete_in = MagicMock()
    mock_delete_in.execute = AsyncMock(return_value=mock_delete_result)
    mock_delete_query.in_.return_value = mock_delete_in
    mock_sentences_table.delete.return_value = mock_delete_query

    # Setup table() to return appropriate table based on table name
    def table_side_effect(table_name):
        if table_name == "sentences":
            return mock_sentences_table
        elif table_name == "problems":
            return mock_problems_table
        return MagicMock()

    mock_client.table.side_effect = table_side_effect

    return mock_client


@pytest.mark.unit
class TestPurgeOrphanedSentencesBasic:
    """Test basic purge orphaned sentences functionality."""

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.require_confirmation")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_purge_orphaned_success(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test successful purge of orphaned sentences."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(
            sentence_count=10, problem_count=2, orphaned_count=3
        )

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, ["--orphaned"])

        assert result.exit_code == 0
        assert "Deleted 3 orphaned sentences" in result.output

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_purge_requires_orphaned_flag(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test that --orphaned flag is required."""
        mock_get_remote.return_value = False
        mock_get_client.return_value = create_mock_supabase_client()

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, [])

        assert result.exit_code == 0
        assert "--orphaned flag is required" in result.output

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.require_confirmation")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_purge_aborted_on_decline(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge aborted when user declines confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = False  # User declines
        mock_get_client.return_value = create_mock_supabase_client(
            sentence_count=5, problem_count=1, orphaned_count=2
        )

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, ["--orphaned"])

        assert result.exit_code == 0
        assert "Aborted" in result.output

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.require_confirmation")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_purge_with_force_skips_confirmation(
        self,
        mock_get_remote,
        mock_confirm,
        mock_get_client,
    ):
        """Test purge with --force skips confirmation."""
        mock_get_remote.return_value = False
        mock_confirm.return_value = True
        mock_get_client.return_value = create_mock_supabase_client(
            sentence_count=5, problem_count=1, orphaned_count=2
        )

        runner = CliRunner()
        result = await runner.invoke(
            purge_orphaned_sentences, ["--orphaned", "--force"]
        )

        assert result.exit_code == 0
        # Verify confirmation was called with force=True
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("force") is True

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_purge_no_sentences_found(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test purge when no sentences exist."""
        mock_get_remote.return_value = False
        mock_get_client.return_value = create_mock_supabase_client(
            sentence_count=0, problem_count=0, orphaned_count=0
        )

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, ["--orphaned"])

        assert result.exit_code == 0
        assert "No sentences found" in result.output

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_purge_no_orphaned_sentences(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test purge when no orphaned sentences exist."""
        mock_get_remote.return_value = False
        mock_get_client.return_value = create_mock_supabase_client(
            sentence_count=5, problem_count=1, orphaned_count=0
        )

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, ["--orphaned"])

        assert result.exit_code == 0
        assert "No orphaned sentences found" in result.output


@pytest.mark.unit
class TestPurgeOrphanedSentencesRemoteForbidden:
    """Test that remote purge is forbidden."""

    @patch("src.cli.sentences.purge.forbid_remote")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_remote_purge_is_forbidden(
        self,
        mock_get_remote,
        mock_forbid_remote,
    ):
        """Test that remote purge is forbidden."""
        mock_get_remote.return_value = True  # Remote mode
        mock_forbid_remote.return_value = True  # Indicates forbidden

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, ["--orphaned"])

        # Command should exit early
        assert result.exit_code == 0
        mock_forbid_remote.assert_called_once_with("lqs sentence purge", True)

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.forbid_remote")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_local_purge_is_allowed(
        self,
        mock_get_remote,
        mock_forbid_remote,
        mock_get_client,
    ):
        """Test that local purge is allowed."""
        mock_get_remote.return_value = False  # Local mode
        mock_forbid_remote.return_value = False  # Not forbidden
        mock_get_client.return_value = create_mock_supabase_client(
            sentence_count=0, problem_count=0, orphaned_count=0
        )

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, ["--orphaned"])

        assert result.exit_code == 0
        mock_forbid_remote.assert_called_once_with("lqs sentence purge", False)


@pytest.mark.unit
class TestPurgeOrphanedSentencesErrorHandling:
    """Test error handling for purge command."""

    @patch("src.cli.sentences.purge.get_supabase_client")
    @patch("src.cli.sentences.purge.get_remote_flag")
    async def test_purge_handles_database_error(
        self,
        mock_get_remote,
        mock_get_client,
    ):
        """Test that purge handles database errors gracefully."""
        mock_get_remote.return_value = False
        mock_get_client.side_effect = Exception("Database connection failed")

        runner = CliRunner()
        result = await runner.invoke(purge_orphaned_sentences, ["--orphaned"])

        assert result.exit_code == 0  # Command doesn't crash
        assert "Error" in result.output
