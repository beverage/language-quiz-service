"""Shared fixtures for verb domain tests."""

import pytest

from src.cache.conjugation_cache import ConjugationCache
from src.cache.verb_cache import VerbCache
from src.clients.supabase import get_supabase_client
from src.repositories.verb_repository import VerbRepository


@pytest.fixture(scope="function")
async def verb_caches(redis_client):
    """Provide VerbCache and ConjugationCache instances for verb tests.

    Loads data from database into the caches before each test.
    Uses unique namespace for test isolation.
    """
    client = await get_supabase_client()
    verb_repo = VerbRepository(client=client)

    # Get unique namespace for this test
    namespace = redis_client._test_namespace

    verb_cache = VerbCache(redis_client, namespace=namespace)
    conjugation_cache = ConjugationCache(redis_client, namespace=namespace)

    # Load caches with data from database
    await verb_cache.load(verb_repo)
    await conjugation_cache.load(verb_repo)

    return {
        "verb_cache": verb_cache,
        "conjugation_cache": conjugation_cache,
    }
