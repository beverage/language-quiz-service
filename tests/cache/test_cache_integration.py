"""Integration tests for cache loading."""

import pytest

from src.cache.api_key_cache import ApiKeyCache
from src.cache.conjugation_cache import ConjugationCache
from src.cache.verb_cache import VerbCache
from src.clients.supabase import get_supabase_client
from src.repositories.api_keys_repository import ApiKeyRepository
from src.repositories.verb_repository import VerbRepository

# NOTE: Service-level integration tests are omitted here because they would
# require using the global singleton cache instances. Those are tested
# via functional/acceptance tests that run against the actual API.


@pytest.fixture
def cache_namespace(redis_client) -> str:
    """Get the unique namespace for this test's cache keys."""
    return redis_client._test_namespace


@pytest.mark.asyncio
class TestCacheStartupIntegration:
    """Test cache loading during application startup."""

    async def test_all_caches_load_successfully(self, redis_client, cache_namespace):
        """All caches should load successfully from database."""
        # Setup
        client = await get_supabase_client()
        verb_repo = VerbRepository(client)
        api_key_repo = ApiKeyRepository(client)

        # Create cache instances with Redis client and namespace
        verb_cache = VerbCache(redis_client, namespace=cache_namespace)
        conj_cache = ConjugationCache(redis_client, namespace=cache_namespace)
        api_key_cache = ApiKeyCache(redis_client, namespace=cache_namespace)

        # Load all caches
        import asyncio

        await asyncio.gather(
            verb_cache.load(verb_repo),
            conj_cache.load(verb_repo),
            api_key_cache.load(api_key_repo),
        )

        # Verify all are loaded
        assert verb_cache.get_stats()["loaded"] is True
        assert conj_cache.get_stats()["loaded"] is True
        assert api_key_cache.get_stats()["loaded"] is True

        # Verify they have data
        assert verb_cache.get_stats()["total_verbs"] > 0
        assert conj_cache.get_stats()["total_conjugations"] > 0
        assert api_key_cache.get_stats()["total_keys"] >= 0  # May be zero in test env

    async def test_cache_stats_accurate_after_load(self, redis_client, cache_namespace):
        """Cache statistics should be accurate after loading."""
        # Setup
        client = await get_supabase_client()
        verb_repo = VerbRepository(client)

        verb_cache = VerbCache(redis_client, namespace=cache_namespace)
        await verb_cache.load(verb_repo)

        stats = verb_cache.get_stats()

        # Verify stats structure
        assert "loaded" in stats
        assert "total_verbs" in stats
        assert "languages" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

        # Verify initial values
        assert stats["loaded"] is True
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == "0.00%"
