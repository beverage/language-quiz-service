"""Tests for CLI safety utilities."""

from unittest.mock import MagicMock, patch

import pytest

from src.cli.utils.safety import (
    forbid_remote,
    get_remote_flag,
    require_confirmation,
)


@pytest.mark.unit
class TestRequireConfirmation:
    """Test cases for require_confirmation function."""

    def test_force_bypasses_confirmation(self):
        """Test that force=True skips all confirmation prompts."""
        result = require_confirmation(
            operation_name="delete everything",
            is_remote=True,
            force=True,
        )
        assert result is True

    def test_force_bypasses_local_confirmation(self):
        """Test that force=True skips local confirmation too."""
        result = require_confirmation(
            operation_name="delete something",
            is_remote=False,
            force=True,
        )
        assert result is True

    @patch("src.cli.utils.safety.click.confirm")
    @patch("src.cli.utils.safety.click.echo")
    def test_remote_shows_warning_and_confirms(self, mock_echo, mock_confirm):
        """Test that remote operations show warning and require confirmation."""
        mock_confirm.return_value = True

        result = require_confirmation(
            operation_name="wipe database",
            is_remote=True,
            force=False,
        )

        assert result is True
        # Verify warning was shown
        echo_calls = [str(call) for call in mock_echo.call_args_list]
        assert any("WARNING" in str(call) for call in echo_calls)
        assert any("REMOTE" in str(call) for call in echo_calls)
        assert any("DESTRUCTIVE" in str(call) for call in echo_calls)
        # Verify confirmation was requested with default=False (cautious)
        mock_confirm.assert_called_once()
        assert mock_confirm.call_args.kwargs.get("default") is False

    @patch("src.cli.utils.safety.click.confirm")
    @patch("src.cli.utils.safety.click.echo")
    def test_remote_denied_returns_false(self, mock_echo, mock_confirm):
        """Test that denying remote confirmation returns False."""
        mock_confirm.return_value = False

        result = require_confirmation(
            operation_name="wipe database",
            is_remote=True,
            force=False,
        )

        assert result is False

    @patch("src.cli.utils.safety.click.confirm")
    def test_local_confirms_with_default_true(self, mock_confirm):
        """Test that local operations confirm with default=True (permissive)."""
        mock_confirm.return_value = True

        result = require_confirmation(
            operation_name="delete something",
            is_remote=False,
            force=False,
        )

        assert result is True
        mock_confirm.assert_called_once()
        # Local operations default to True (yes)
        assert mock_confirm.call_args.kwargs.get("default") is True

    @patch("src.cli.utils.safety.click.confirm")
    def test_local_denied_returns_false(self, mock_confirm):
        """Test that denying local confirmation returns False."""
        mock_confirm.return_value = False

        result = require_confirmation(
            operation_name="delete something",
            is_remote=False,
            force=False,
        )

        assert result is False

    @patch("src.cli.utils.safety.click.confirm")
    @patch("src.cli.utils.safety.click.echo")
    def test_item_count_included_in_message(self, mock_echo, mock_confirm):
        """Test that item_count is included in confirmation message."""
        mock_confirm.return_value = True

        require_confirmation(
            operation_name="delete problems",
            is_remote=True,
            force=False,
            item_count=42,
        )

        # Verify "42 items" appears in the output
        echo_calls = " ".join(str(call) for call in mock_echo.call_args_list)
        assert "42 items" in echo_calls


@pytest.mark.unit
class TestForbidRemote:
    """Test cases for forbid_remote function."""

    @patch("src.cli.utils.safety.click.echo")
    def test_remote_is_forbidden(self, mock_echo):
        """Test that remote operations are forbidden."""
        result = forbid_remote(
            operation_name="database wipe",
            is_remote=True,
        )

        assert result is True
        # Verify error message was shown
        echo_calls = " ".join(str(call) for call in mock_echo.call_args_list)
        assert "FORBIDDEN" in echo_calls
        assert "--remote" in echo_calls

    def test_local_is_allowed(self):
        """Test that local operations are allowed."""
        result = forbid_remote(
            operation_name="database wipe",
            is_remote=False,
        )

        assert result is False


@pytest.mark.unit
class TestGetRemoteFlag:
    """Test cases for get_remote_flag function."""

    def test_gets_remote_from_root_context(self):
        """Test extracting remote flag from root context."""
        # Create mock context chain
        mock_root = MagicMock()
        mock_root.obj = {"remote": True, "service_url": "http://example.com"}

        mock_ctx = MagicMock()
        mock_ctx.find_root.return_value = mock_root

        result = get_remote_flag(mock_ctx)

        assert result is True

    def test_gets_false_when_not_remote(self):
        """Test returning False when remote flag is not set."""
        mock_root = MagicMock()
        mock_root.obj = {"remote": False}

        mock_ctx = MagicMock()
        mock_ctx.find_root.return_value = mock_root

        result = get_remote_flag(mock_ctx)

        assert result is False

    def test_returns_false_when_obj_is_none(self):
        """Test returning False when context obj is None."""
        mock_root = MagicMock()
        mock_root.obj = None

        mock_ctx = MagicMock()
        mock_ctx.find_root.return_value = mock_root

        result = get_remote_flag(mock_ctx)

        assert result is False

    def test_returns_false_when_remote_key_missing(self):
        """Test returning False when remote key is missing from obj."""
        mock_root = MagicMock()
        mock_root.obj = {"service_url": "http://example.com"}

        mock_ctx = MagicMock()
        mock_ctx.find_root.return_value = mock_root

        result = get_remote_flag(mock_ctx)

        assert result is False
