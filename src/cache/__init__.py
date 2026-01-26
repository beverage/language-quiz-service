"""Cache module for Redis-backed data caching.

All cache classes require a Redis client to be passed in the constructor.
Use FastAPI dependencies (src.core.dependencies) to get cache instances.
"""

from src.cache.api_key_cache import ApiKeyCache
from src.cache.conjugation_cache import ConjugationCache
from src.cache.verb_cache import VerbCache

__all__ = [
    "VerbCache",
    "ConjugationCache",
    "ApiKeyCache",
]
