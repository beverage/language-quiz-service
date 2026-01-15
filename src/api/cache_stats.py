"""Cache statistics and management API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.cache.api_key_cache import ApiKeyCache
from src.cache.conjugation_cache import ConjugationCache
from src.cache.verb_cache import VerbCache
from src.clients.supabase import get_supabase_client
from src.core.auth import get_current_api_key
from src.core.dependencies import (
    get_api_key_cache,
    get_conjugation_cache,
    get_verb_cache,
)
from src.repositories.api_keys_repository import ApiKeyRepository
from src.repositories.verb_repository import VerbRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cache"])


@router.get(
    "/cache/stats",
    summary="Get cache statistics",
    description="""
    Get current cache statistics including hit rates and data counts.

    Useful for monitoring cache performance and troubleshooting.
    """,
    responses={
        200: {
            "description": "Cache statistics",
            "content": {
                "application/json": {
                    "example": {
                        "verb_cache": {
                            "loaded": True,
                            "total_verbs": 1542,
                            "languages": 1,
                            "hits": 15234,
                            "misses": 45,
                            "hit_rate": "99.71%",
                        },
                        "conjugation_cache": {
                            "loaded": True,
                            "total_conjugations": 10794,
                            "unique_verbs": 1542,
                            "hits": 8562,
                            "misses": 12,
                            "hit_rate": "99.86%",
                        },
                        "api_key_cache": {
                            "loaded": True,
                            "total_keys": 3,
                            "active_keys": 3,
                            "hits": 25678,
                            "misses": 3,
                            "hit_rate": "99.99%",
                        },
                    }
                }
            },
        }
    },
)
async def get_cache_stats(
    verb_cache: VerbCache | None = Depends(get_verb_cache),
    conjugation_cache: ConjugationCache | None = Depends(get_conjugation_cache),
    api_key_cache: ApiKeyCache | None = Depends(get_api_key_cache),
):
    """
    Get cache statistics for monitoring and debugging.

    Returns hit rates, data counts, and load status for all caches.
    """
    unavailable = {"loaded": False, "error": "Redis not available"}
    return {
        "verb_cache": verb_cache.get_stats() if verb_cache else unavailable,
        "conjugation_cache": conjugation_cache.get_stats()
        if conjugation_cache
        else unavailable,
        "api_key_cache": api_key_cache.get_stats() if api_key_cache else unavailable,
    }


@router.post(
    "/cache/reload",
    summary="Reload caches from database",
    description="""
    Force reload all caches from the database.

    Useful after making direct database changes outside the API.
    Requires admin permission.
    """,
    responses={
        200: {
            "description": "Cache reload results",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Caches reloaded successfully",
                        "verb_cache": {"total_verbs": 1542, "languages": 1},
                        "conjugation_cache": {
                            "total_conjugations": 10794,
                            "unique_verbs": 1542,
                        },
                        "api_key_cache": {"total_keys": 3, "active_keys": 3},
                    }
                }
            },
        },
        403: {"description": "Admin permission required"},
    },
)
async def reload_caches(
    verb_cache: VerbCache | None = Depends(get_verb_cache),
    conjugation_cache: ConjugationCache | None = Depends(get_conjugation_cache),
    api_key_cache: ApiKeyCache | None = Depends(get_api_key_cache),
    current_key: dict = Depends(get_current_api_key),
):
    """
    Reload all caches from the database.

    Requires admin permission.
    """
    # Check admin permission
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")

    # Check if Redis is available
    if not verb_cache or not conjugation_cache or not api_key_cache:
        raise HTTPException(
            status_code=503, detail="Redis not available for cache reload"
        )

    # Get database client and repositories
    client = await get_supabase_client()
    verb_repo = VerbRepository(client)
    api_key_repo = ApiKeyRepository(client)

    # Reload all caches
    await verb_cache.reload(verb_repo)
    await conjugation_cache.reload(verb_repo)
    await api_key_cache.reload(api_key_repo)

    return {
        "message": "Caches reloaded successfully",
        "verb_cache": verb_cache.get_stats(),
        "conjugation_cache": conjugation_cache.get_stats(),
        "api_key_cache": api_key_cache.get_stats(),
    }
