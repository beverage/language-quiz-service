"""Tests for CLI cache commands."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asyncclick.testing import CliRunner

from src.cli.cache.commands import cache_stats, reload_cache


@pytest.fixture
def mock_verb_cache_stats():
    """Sample verb cache stats."""
    return {
        "loaded": True,
        "total_verbs": 150,
        "languages": 1,
        "hits": 500,
        "misses": 10,
        "hit_rate": "98.04%",
    }


@pytest.fixture
def mock_conjugation_cache_stats():
    """Sample conjugation cache stats."""
    return {
        "loaded": True,
        "total_conjugations": 3000,
        "unique_verbs": 150,
        "hits": 1000,
        "misses": 50,
        "hit_rate": "95.24%",
    }


@pytest.fixture
def mock_api_key_cache_stats():
    """Sample API key cache stats."""
    return {
        "loaded": True,
        "total_keys": 5,
        "active_keys": 4,
        "hits": 200,
        "misses": 2,
        "hit_rate": "99.01%",
    }


@pytest.mark.unit
class TestCacheStats:
    """Test cache stats command."""

    @patch("src.cli.cache.commands.api_key_cache")
    @patch("src.cli.cache.commands.conjugation_cache")
    @patch("src.cli.cache.commands.verb_cache")
    async def test_cache_stats_displays_all_caches(
        self,
        mock_verb_cache,
        mock_conj_cache,
        mock_api_cache,
        mock_verb_cache_stats,
        mock_conjugation_cache_stats,
        mock_api_key_cache_stats,
    ):
        """Test that stats displays all cache information."""
        mock_verb_cache.get_stats.return_value = mock_verb_cache_stats
        mock_conj_cache.get_stats.return_value = mock_conjugation_cache_stats
        mock_api_cache.get_stats.return_value = mock_api_key_cache_stats

        runner = CliRunner()
        result = await runner.invoke(cache_stats, [])

        assert result.exit_code == 0
        # Verify verb cache stats
        assert "Verb Cache" in result.output
        assert "150" in result.output  # total_verbs
        assert "98.04%" in result.output  # hit_rate

        # Verify conjugation cache stats
        assert "Conjugation Cache" in result.output
        assert "3000" in result.output  # total_conjugations

        # Verify API key cache stats
        assert "API Key Cache" in result.output
        assert "5" in result.output  # total_keys

    @patch("src.cli.cache.commands.api_key_cache")
    @patch("src.cli.cache.commands.conjugation_cache")
    @patch("src.cli.cache.commands.verb_cache")
    async def test_cache_stats_shows_not_loaded(
        self,
        mock_verb_cache,
        mock_conj_cache,
        mock_api_cache,
    ):
        """Test that stats shows when caches are not loaded."""
        mock_verb_cache.get_stats.return_value = {
            "loaded": False,
            "total_verbs": 0,
            "languages": 0,
            "hits": 0,
            "misses": 0,
            "hit_rate": "0.00%",
        }
        mock_conj_cache.get_stats.return_value = {
            "loaded": False,
            "total_conjugations": 0,
            "unique_verbs": 0,
            "hits": 0,
            "misses": 0,
            "hit_rate": "0.00%",
        }
        mock_api_cache.get_stats.return_value = {
            "loaded": False,
            "total_keys": 0,
            "active_keys": 0,
            "hits": 0,
            "misses": 0,
            "hit_rate": "0.00%",
        }

        runner = CliRunner()
        result = await runner.invoke(cache_stats, [])

        assert result.exit_code == 0
        assert "False" in result.output  # loaded: False


@pytest.mark.unit
class TestReloadCache:
    """Test cache reload command."""

    @patch("src.cli.cache.commands.get_supabase_client")
    @patch("src.cli.cache.commands.api_key_cache")
    @patch("src.cli.cache.commands.conjugation_cache")
    @patch("src.cli.cache.commands.verb_cache")
    @patch("src.cli.cache.commands.VerbRepository")
    @patch("src.cli.cache.commands.ApiKeyRepository")
    async def test_reload_all_caches(
        self,
        mock_api_repo_class,
        mock_verb_repo_class,
        mock_verb_cache,
        mock_conj_cache,
        mock_api_cache,
        mock_get_client,
    ):
        """Test reloading all caches."""
        mock_get_client.return_value = MagicMock()
        mock_verb_cache.reload = AsyncMock()
        mock_verb_cache.get_stats.return_value = {"total_verbs": 100}
        mock_conj_cache.reload = AsyncMock()
        mock_conj_cache.get_stats.return_value = {"total_conjugations": 2000}
        mock_api_cache.reload = AsyncMock()
        mock_api_cache.get_stats.return_value = {"total_keys": 3}

        runner = CliRunner()
        result = await runner.invoke(reload_cache, ["all"])

        assert result.exit_code == 0
        assert "Reloading verb cache" in result.output
        assert "Reloading conjugation cache" in result.output
        assert "Reloading API key cache" in result.output
        assert "Cache reload complete" in result.output
        mock_verb_cache.reload.assert_called_once()
        mock_conj_cache.reload.assert_called_once()
        mock_api_cache.reload.assert_called_once()

    @patch("src.cli.cache.commands.get_supabase_client")
    @patch("src.cli.cache.commands.verb_cache")
    @patch("src.cli.cache.commands.VerbRepository")
    async def test_reload_verbs_only(
        self,
        mock_verb_repo_class,
        mock_verb_cache,
        mock_get_client,
    ):
        """Test reloading only verb cache."""
        mock_get_client.return_value = MagicMock()
        mock_verb_cache.reload = AsyncMock()
        mock_verb_cache.get_stats.return_value = {"total_verbs": 100}

        runner = CliRunner()
        result = await runner.invoke(reload_cache, ["verbs"])

        assert result.exit_code == 0
        assert "Reloading verb cache" in result.output
        assert "Reloading conjugation cache" not in result.output
        assert "Reloading API key cache" not in result.output
        mock_verb_cache.reload.assert_called_once()

    @patch("src.cli.cache.commands.get_supabase_client")
    @patch("src.cli.cache.commands.api_key_cache")
    @patch("src.cli.cache.commands.ApiKeyRepository")
    async def test_reload_api_keys_only(
        self,
        mock_api_repo_class,
        mock_api_cache,
        mock_get_client,
    ):
        """Test reloading only API key cache."""
        mock_get_client.return_value = MagicMock()
        mock_api_cache.reload = AsyncMock()
        mock_api_cache.get_stats.return_value = {"total_keys": 5}

        runner = CliRunner()
        result = await runner.invoke(reload_cache, ["api-keys"])

        assert result.exit_code == 0
        assert "Reloading API key cache" in result.output
        assert "Reloading verb cache" not in result.output
        mock_api_cache.reload.assert_called_once()

    @patch("src.cli.cache.commands.get_supabase_client")
    async def test_reload_handles_database_error(self, mock_get_client):
        """Test that reload handles database errors gracefully."""
        mock_get_client.side_effect = Exception("Database connection failed")

        runner = CliRunner()
        result = await runner.invoke(reload_cache, ["all"])

        assert result.exit_code == 0  # Command doesn't crash
        assert "Error" in result.output

    @patch("src.cli.cache.commands.get_supabase_client")
    @patch("src.cli.cache.commands.verb_cache")
    @patch("src.cli.cache.commands.conjugation_cache")
    @patch("src.cli.cache.commands.api_key_cache")
    @patch("src.cli.cache.commands.VerbRepository")
    @patch("src.cli.cache.commands.ApiKeyRepository")
    async def test_reload_default_is_all(
        self,
        mock_api_repo_class,
        mock_verb_repo_class,
        mock_api_cache,
        mock_conj_cache,
        mock_verb_cache,
        mock_get_client,
    ):
        """Test that default reload reloads all caches."""
        mock_get_client.return_value = MagicMock()
        mock_verb_cache.reload = AsyncMock()
        mock_verb_cache.get_stats.return_value = {"total_verbs": 100}
        mock_conj_cache.reload = AsyncMock()
        mock_conj_cache.get_stats.return_value = {"total_conjugations": 2000}
        mock_api_cache.reload = AsyncMock()
        mock_api_cache.get_stats.return_value = {"total_keys": 3}

        runner = CliRunner()
        result = await runner.invoke(reload_cache, [])  # No argument = default to "all"

        assert result.exit_code == 0
        mock_verb_cache.reload.assert_called_once()
        mock_conj_cache.reload.assert_called_once()
        mock_api_cache.reload.assert_called_once()
