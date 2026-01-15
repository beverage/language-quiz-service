"""Redis-backed cache for API keys."""

import logging
from uuid import UUID

import redis.asyncio as aioredis
from opentelemetry import trace

from src.schemas.api_keys import ApiKey

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ApiKeyCache:
    """
    Redis-backed cache for API keys.

    Uses Redis for:
    - Primary index: apikey:id:{uuid} -> ApiKey JSON
    - Prefix index: apikey:prefix:{prefix} -> ApiKey JSON
    - Hash index: apikey:hash:{hash} -> ApiKey JSON

    Optimized for authentication lookups by key_prefix (hottest path).
    This is a thin wrapper around Redis - no in-memory state is kept.
    Create instances as needed via dependency injection.

    Args:
        redis_client: The Redis client to use for storage.
        namespace: Optional namespace prefix for key isolation (useful for testing).
    """

    BASE_PREFIX = "apikey"

    def __init__(self, redis_client: aioredis.Redis, namespace: str = ""):
        self._redis = redis_client
        self._loaded = False
        self._namespace = namespace
        self.PREFIX = (
            f"{namespace}{self.BASE_PREFIX}" if namespace else self.BASE_PREFIX
        )

        # Metrics (per-instance, mainly for debugging)
        self._hits = 0
        self._misses = 0
        self._key_count = 0
        self._active_count = 0

    def _id_key(self, key_id: UUID) -> str:
        """Key for lookup by UUID."""
        return f"{self.PREFIX}:id:{key_id}"

    def _prefix_key(self, key_prefix: str) -> str:
        """Key for lookup by prefix (authentication hot path)."""
        return f"{self.PREFIX}:prefix:{key_prefix}"

    def _hash_key(self, key_hash: str) -> str:
        """Key for lookup by hash."""
        return f"{self.PREFIX}:hash:{key_hash}"

    async def load(self, repository) -> None:
        """Load all API keys into Redis cache at startup."""
        with tracer.start_as_current_span("api_key_cache.load"):
            if not hasattr(repository, "get_all_api_keys"):
                raise TypeError("Repository must have get_all_api_keys method")

            logger.info("Loading API keys into Redis cache...")
            api_keys = await repository.get_all_api_keys(
                limit=1000, include_inactive=True
            )

            # Clear existing keys
            await self._clear_cache()

            # Use pipeline for batch operations
            pipe = self._redis.pipeline()
            active_count = 0

            for key in api_keys:
                key_json = key.model_dump_json()

                # Store in all indexes
                pipe.set(self._id_key(key.id), key_json)
                pipe.set(self._prefix_key(key.key_prefix), key_json)
                pipe.set(self._hash_key(key.key_hash), key_json)

                if key.is_active:
                    active_count += 1

            await pipe.execute()

            self._loaded = True
            self._key_count = len(api_keys)
            self._active_count = active_count
            logger.info(
                f"✅ Loaded {len(api_keys)} API keys into Redis cache "
                f"({active_count} active)"
            )

    async def _clear_cache(self) -> None:
        """Clear all API key cache keys using SCAN (non-blocking)."""
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor, match=f"{self.PREFIX}:*", count=100
            )
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break

    async def is_loaded(self) -> bool:
        """Check if cache has data by checking if any API key keys exist."""
        cursor, keys = await self._redis.scan(0, match=f"{self.PREFIX}:id:*", count=1)
        return len(keys) > 0

    async def get_by_id(self, key_id: UUID) -> ApiKey | None:
        """Get an API key by ID from cache."""
        data = await self._redis.get(self._id_key(key_id))

        if data:
            self._hits += 1
            return ApiKey.model_validate_json(data)

        self._misses += 1
        return None

    async def get_by_prefix(self, key_prefix: str) -> ApiKey | None:
        """
        Get an API key by prefix from cache.

        This is the most common lookup path during authentication.
        Only returns active keys.
        """
        data = await self._redis.get(self._prefix_key(key_prefix))

        if data:
            key = ApiKey.model_validate_json(data)
            if key.is_active:
                self._hits += 1
                return key

        self._misses += 1
        return None

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        """Get an API key by hash from cache. Only returns active keys."""
        data = await self._redis.get(self._hash_key(key_hash))

        if data:
            key = ApiKey.model_validate_json(data)
            if key.is_active:
                self._hits += 1
                return key

        self._misses += 1
        return None

    async def refresh_key(self, api_key: ApiKey) -> None:
        """Add or update an API key in the cache."""
        # Get old key if exists (to remove old prefix/hash if they changed)
        old_data = await self._redis.get(self._id_key(api_key.id))
        if old_data:
            old_key = ApiKey.model_validate_json(old_data)
            # Remove old indexes if they differ
            if old_key.key_prefix != api_key.key_prefix:
                await self._redis.delete(self._prefix_key(old_key.key_prefix))
            if old_key.key_hash != api_key.key_hash:
                await self._redis.delete(self._hash_key(old_key.key_hash))

        # Store in all indexes
        key_json = api_key.model_dump_json()
        pipe = self._redis.pipeline()
        pipe.set(self._id_key(api_key.id), key_json)
        pipe.set(self._prefix_key(api_key.key_prefix), key_json)
        pipe.set(self._hash_key(api_key.key_hash), key_json)
        await pipe.execute()

        logger.debug(f"Refreshed API key {api_key.name} in cache")

    async def invalidate_key(self, key_id: UUID) -> None:
        """Remove an API key from the cache."""
        # Get key first to know which indexes to remove
        data = await self._redis.get(self._id_key(key_id))
        if data:
            key = ApiKey.model_validate_json(data)

            pipe = self._redis.pipeline()
            pipe.delete(self._id_key(key_id))
            pipe.delete(self._prefix_key(key.key_prefix))
            pipe.delete(self._hash_key(key.key_hash))
            await pipe.execute()

            logger.debug(f"Invalidated API key {key_id} from cache")

    async def reload(self, repository) -> None:
        """Reload all API keys from database."""
        logger.info("Reloading API key cache from database...")
        await self.load(repository)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "loaded": self._loaded,
            "total_keys": self._key_count,
            "active_keys": self._active_count,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }
