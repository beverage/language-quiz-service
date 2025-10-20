"""Cache statistics API endpoint."""

import logging

from fastapi import APIRouter

from src.cache import api_key_cache, conjugation_cache, verb_cache

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
async def get_cache_stats():
    """
    Get cache statistics for monitoring and debugging.

    Returns hit rates, data counts, and load status for all caches.
    """
    return {
        "verb_cache": verb_cache.get_stats(),
        "conjugation_cache": conjugation_cache.get_stats(),
        "api_key_cache": api_key_cache.get_stats(),
    }
