"""Shared fixtures for verb domain tests."""

import pytest


@pytest.fixture(scope="function", autouse=True)
async def ensure_verb_cache_loaded():
    """Ensure verb cache is loaded before each verb test.

    Only verb service tests need the global verb_cache singleton pre-loaded,
    specifically for tests that call get_random_verb() which requires the cache
    to be populated. Other tests create their own VerbService instances or use
    repositories directly.
    """
    from src.cache.verb_cache import verb_cache
    from src.clients.supabase import get_supabase_client
    from src.repositories.verb_repository import VerbRepository

    # Force reload to get latest test data
    stats = verb_cache.get_stats()
    if not stats["loaded"] or stats["total_verbs"] == 0:
        try:
            client = await get_supabase_client()
            verb_repo = VerbRepository(client=client)
            await verb_cache.load(verb_repo)
        except Exception as e:
            # If loading fails, log but continue
            # Tests that need it will fail with clear errors
            print(f"Warning: Failed to load verb cache: {e}")
            import traceback

            traceback.print_exc()

    yield
