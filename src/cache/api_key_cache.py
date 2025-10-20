"""In-memory cache for API keys."""

import asyncio
import logging
from uuid import UUID

from opentelemetry import trace

from src.schemas.api_keys import ApiKey

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ApiKeyCache:
    """
    In-memory cache for API keys.

    Optimized for authentication lookups by key_prefix.
    This is the hottest path in the application.
    """

    def __init__(self):
        # Primary index: by UUID
        self._keys_by_id: dict[UUID, ApiKey] = {}

        # Authentication index: by key_prefix (first 12 chars)
        self._keys_by_prefix: dict[str, ApiKey] = {}

        # Authentication index: by key_hash (for verification)
        self._keys_by_hash: dict[str, ApiKey] = {}

        self._loaded = False
        self._lock = asyncio.Lock()

        # Metrics
        self._hits = 0
        self._misses = 0

    async def load(self, repository):
        """Load all API keys into cache at startup."""
        with tracer.start_as_current_span("api_key_cache.load"):
            async with self._lock:
                # Duck typing: check for the method we need instead of isinstance
                if not hasattr(repository, "get_all_api_keys"):
                    raise TypeError("Repository must have get_all_api_keys method")

                logger.info("Loading API keys into cache...")
                api_keys = await repository.get_all_api_keys(
                    limit=1000, include_inactive=True
                )

                self._keys_by_id.clear()
                self._keys_by_prefix.clear()
                self._keys_by_hash.clear()

                for key in api_keys:
                    self._add_key_to_indexes(key)

                self._loaded = True
                active_count = sum(1 for k in api_keys if k.is_active)
                logger.info(
                    f"✅ Loaded {len(api_keys)} API keys into cache "
                    f"({active_count} active)"
                )

    def _add_key_to_indexes(self, api_key: ApiKey):
        """Add an API key to all indexes (internal helper)."""
        self._keys_by_id[api_key.id] = api_key
        self._keys_by_prefix[api_key.key_prefix] = api_key
        self._keys_by_hash[api_key.key_hash] = api_key

    def _remove_key_from_indexes(self, api_key: ApiKey):
        """Remove an API key from all indexes (internal helper)."""
        self._keys_by_id.pop(api_key.id, None)
        self._keys_by_prefix.pop(api_key.key_prefix, None)
        self._keys_by_hash.pop(api_key.key_hash, None)

    async def get_by_id(self, key_id: UUID) -> ApiKey | None:
        """Get an API key by ID from cache."""
        if not self._loaded:
            self._misses += 1
            return None

        key = self._keys_by_id.get(key_id)
        if key:
            self._hits += 1
        else:
            self._misses += 1
        return key

    async def get_by_prefix(self, key_prefix: str) -> ApiKey | None:
        """
        Get an API key by prefix from cache.

        This is the most common lookup path during authentication.
        """
        if not self._loaded:
            self._misses += 1
            return None

        key = self._keys_by_prefix.get(key_prefix)
        if key and key.is_active:
            self._hits += 1
            return key

        self._misses += 1
        return None

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        """Get an API key by hash from cache."""
        if not self._loaded:
            self._misses += 1
            return None

        key = self._keys_by_hash.get(key_hash)
        if key and key.is_active:
            self._hits += 1
            return key

        self._misses += 1
        return None

    async def refresh_key(self, api_key: ApiKey):
        """Add or update an API key in the cache."""
        async with self._lock:
            # Remove old version if it exists
            if api_key.id in self._keys_by_id:
                old_key = self._keys_by_id[api_key.id]
                self._remove_key_from_indexes(old_key)

            # Add new version
            self._add_key_to_indexes(api_key)
            logger.debug(f"Refreshed API key {api_key.name} in cache")

    async def invalidate_key(self, key_id: UUID):
        """Remove an API key from the cache."""
        async with self._lock:
            if key_id in self._keys_by_id:
                key = self._keys_by_id[key_id]
                self._remove_key_from_indexes(key)
                logger.debug(f"Invalidated API key {key_id} from cache")

    async def reload(self, repository):
        """Reload all API keys from database (for NOTIFY/LISTEN)."""
        logger.info("Reloading API key cache from database...")
        await self.load(repository)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        active_keys = sum(1 for k in self._keys_by_id.values() if k.is_active)

        return {
            "loaded": self._loaded,
            "total_keys": len(self._keys_by_id),
            "active_keys": active_keys,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


# Global singleton instance
api_key_cache = ApiKeyCache()
