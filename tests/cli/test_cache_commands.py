"""Tests for CLI cache commands."""

from unittest.mock import patch

import pytest
from asyncclick.testing import CliRunner
from httpx import Response

from src.cli.cache.commands import cache_stats, reload_cache


@pytest.fixture
def mock_stats_response():
    """Sample cache stats API response."""
    return {
        "verb_cache": {
            "loaded": True,
            "total_verbs": 150,
            "languages": 1,
            "hits": 500,
            "misses": 10,
            "hit_rate": "98.04%",
        },
        "conjugation_cache": {
            "loaded": True,
            "total_conjugations": 3000,
            "unique_verbs": 150,
            "hits": 1000,
            "misses": 50,
            "hit_rate": "95.24%",
        },
        "api_key_cache": {
            "loaded": True,
            "total_keys": 5,
            "active_keys": 4,
            "hits": 200,
            "misses": 2,
            "hit_rate": "99.01%",
        },
    }


@pytest.mark.unit
class TestCacheStats:
    """Test cache stats command."""

    @patch("src.cli.cache.commands.httpx.AsyncClient")
    async def test_cache_stats_displays_all_caches(
        self, mock_client_class, mock_stats_response
    ):
        """Test that stats displays all cache information."""
        mock_response = Response(200, json=mock_stats_response)
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get.return_value = mock_response

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

    @patch("src.cli.cache.commands.httpx.AsyncClient")
    async def test_cache_stats_shows_not_loaded(self, mock_client_class):
        """Test that stats shows when caches are not loaded."""
        not_loaded_response = {
            "verb_cache": {
                "loaded": False,
                "total_verbs": 0,
                "languages": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": "0.00%",
            },
            "conjugation_cache": {
                "loaded": False,
                "total_conjugations": 0,
                "unique_verbs": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": "0.00%",
            },
            "api_key_cache": {
                "loaded": False,
                "total_keys": 0,
                "active_keys": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": "0.00%",
            },
        }
        mock_response = Response(200, json=not_loaded_response)
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(cache_stats, [])

        assert result.exit_code == 0
        assert "False" in result.output  # loaded: False

    @patch("src.cli.cache.commands.httpx.AsyncClient")
    async def test_cache_stats_handles_auth_required(self, mock_client_class):
        """Test that stats handles 401 response."""
        mock_response = Response(401, text="Unauthorized")
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(cache_stats, [])

        assert result.exit_code == 0
        assert "Authentication required" in result.output


@pytest.mark.unit
class TestReloadCache:
    """Test cache reload command."""

    @patch("src.cli.cache.commands.httpx.AsyncClient")
    async def test_reload_all_caches(self, mock_client_class):
        """Test reloading all caches."""
        reload_response = {
            "message": "Caches reloaded successfully",
            "verb_cache": {"total_verbs": 100},
            "conjugation_cache": {"total_conjugations": 2000},
            "api_key_cache": {"total_keys": 3},
        }
        mock_response = Response(200, json=reload_response)
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.post.return_value = mock_response

        runner = CliRunner()
        # Set API key env var for reload
        with patch.dict("os.environ", {"LQS_API_KEY": "test_key"}):
            result = await runner.invoke(reload_cache, [])

        assert result.exit_code == 0
        assert "Caches reloaded" in result.output

    @patch("src.cli.cache.commands.httpx.AsyncClient")
    async def test_reload_handles_auth_error(self, mock_client_class):
        """Test that reload handles 401 response."""
        mock_response = Response(401, text="Unauthorized")
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.post.return_value = mock_response

        runner = CliRunner()
        with patch.dict("os.environ", {"LQS_API_KEY": "test_key"}):
            result = await runner.invoke(reload_cache, [])

        assert result.exit_code == 0
        assert "Authentication failed" in result.output

    @patch("src.cli.cache.commands.httpx.AsyncClient")
    async def test_reload_handles_permission_error(self, mock_client_class):
        """Test that reload handles 403 response."""
        mock_response = Response(403, text="Forbidden")
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.post.return_value = mock_response

        runner = CliRunner()
        with patch.dict("os.environ", {"LQS_API_KEY": "test_key"}):
            result = await runner.invoke(reload_cache, [])

        assert result.exit_code == 0
        assert "Admin permission required" in result.output

    async def test_reload_requires_api_key(self):
        """Test that reload requires API key."""
        runner = CliRunner()
        with patch.dict("os.environ", {}, clear=True):
            # Remove LQS_API_KEY if it exists
            result = await runner.invoke(reload_cache, [])

        assert result.exit_code == 0
        assert "Admin API key required" in result.output
