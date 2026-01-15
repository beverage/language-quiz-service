"""Tests for ApiKeyCache."""

from datetime import UTC, datetime

import pytest

from src.cache.api_key_cache import ApiKeyCache
from src.schemas.api_keys import ApiKey


@pytest.fixture
def cache_namespace(redis_client) -> str:
    """Get the unique namespace for this test's cache keys."""
    return redis_client._test_namespace


@pytest.fixture
def sample_api_keys():
    """Create sample API keys for testing."""
    now = datetime.now(UTC)
    return [
        ApiKey(
            id="00000000-0000-0000-0000-000000000001",
            key_hash="$2b$12$test_hash_1",
            key_prefix="sk_live_abc1",
            name="Test Key 1",
            description="Test key for testing",
            client_name="Test Client",
            is_active=True,
            permissions_scope=["read"],
            usage_count=100,
            rate_limit_rpm=100,
            created_at=now,
            updated_at=now,
        ),
        ApiKey(
            id="00000000-0000-0000-0000-000000000002",
            key_hash="$2b$12$test_hash_2",
            key_prefix="sk_live_xyz2",
            name="Test Key 2",
            description="Another test key",
            client_name="Test Client 2",
            is_active=True,
            permissions_scope=["read", "write"],
            usage_count=50,
            rate_limit_rpm=200,
            created_at=now,
            updated_at=now,
        ),
        ApiKey(
            id="00000000-0000-0000-0000-000000000003",
            key_hash="$2b$12$test_hash_3",
            key_prefix="sk_live_old3",
            name="Inactive Key",
            description="Revoked key",
            client_name="Old Client",
            is_active=False,  # Inactive
            permissions_scope=["read"],
            usage_count=999,
            rate_limit_rpm=100,
            created_at=now,
            updated_at=now,
        ),
    ]


@pytest.fixture
def mock_repository(sample_api_keys):
    """Create a mock API key repository."""

    class MockApiKeyRepository:
        async def get_all_api_keys(self, limit=1000, include_inactive=True):
            return sample_api_keys

    return MockApiKeyRepository()


@pytest.mark.asyncio
class TestApiKeyCache:
    """Test ApiKeyCache functionality."""

    async def test_cache_initially_not_loaded(self, redis_client, cache_namespace):
        """Cache should not be loaded initially."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        stats = cache.get_stats()

        assert stats["loaded"] is False
        assert stats["total_keys"] == 0

    async def test_load_api_keys(self, redis_client, cache_namespace, mock_repository, sample_api_keys):
        """Should load API keys into cache."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        stats = cache.get_stats()
        assert stats["loaded"] is True
        assert stats["total_keys"] == len(sample_api_keys)
        assert stats["active_keys"] == 2  # Only 2 are active

    async def test_get_by_id_hit(self, redis_client, cache_namespace, mock_repository, sample_api_keys):
        """Should return API key from cache by ID."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        key = await cache.get_by_id(sample_api_keys[0].id)
        assert key is not None
        assert key.name == "Test Key 1"

        stats = cache.get_stats()
        assert stats["hits"] == 1

    async def test_get_by_prefix_hit(self, redis_client, cache_namespace, mock_repository):
        """Should return API key from cache by prefix."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        key = await cache.get_by_prefix("sk_live_abc1")
        assert key is not None
        assert key.name == "Test Key 1"
        assert key.is_active is True

    async def test_get_by_prefix_inactive(self, redis_client, cache_namespace, mock_repository):
        """Should return None for inactive key by prefix."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        # Inactive key should return None
        key = await cache.get_by_prefix("sk_live_old3")
        assert key is None

        stats = cache.get_stats()
        assert stats["misses"] == 1

    async def test_get_by_hash_hit(self, redis_client, cache_namespace, mock_repository):
        """Should return API key from cache by hash."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        key = await cache.get_by_hash("$2b$12$test_hash_1")
        assert key is not None
        assert key.name == "Test Key 1"

    async def test_get_by_hash_inactive(self, redis_client, cache_namespace, mock_repository):
        """Should return None for inactive key by hash."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        key = await cache.get_by_hash("$2b$12$test_hash_3")
        assert key is None

    async def test_refresh_key_new(self, redis_client, cache_namespace, mock_repository):
        """Should add new API key to cache."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        now = datetime.now(UTC)
        new_key = ApiKey(
            id="00000000-0000-0000-0000-000000000099",
            key_hash="$2b$12$test_hash_99",
            key_prefix="sk_live_new9",
            name="New Key",
            description="Newly created key",
            client_name="New Client",
            is_active=True,
            permissions_scope=["admin"],
            usage_count=0,
            rate_limit_rpm=500,
            created_at=now,
            updated_at=now,
        )

        await cache.refresh_key(new_key)

        # Verify it's in cache
        key = await cache.get_by_prefix("sk_live_new9")
        assert key is not None
        assert key.name == "New Key"

    async def test_refresh_key_update(
        self, redis_client, cache_namespace, mock_repository, sample_api_keys
    ):
        """Should update existing API key in cache."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        # Update the key
        now = datetime.now(UTC)
        updated_key = ApiKey(
            id=sample_api_keys[0].id,
            key_hash=sample_api_keys[0].key_hash,
            key_prefix=sample_api_keys[0].key_prefix,
            name="Updated Key Name",  # Changed
            description="Updated description",
            client_name="Test Client",
            is_active=True,
            permissions_scope=["read", "write", "admin"],  # Changed
            usage_count=200,
            rate_limit_rpm=100,
            created_at=now,
            updated_at=now,
        )

        await cache.refresh_key(updated_key)

        # Verify it's updated
        key = await cache.get_by_id(sample_api_keys[0].id)
        assert key.name == "Updated Key Name"
        assert "admin" in key.permissions_scope

    async def test_invalidate_key(self, redis_client, cache_namespace, mock_repository, sample_api_keys):
        """Should remove API key from cache."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        # Verify key exists
        key = await cache.get_by_id(sample_api_keys[0].id)
        assert key is not None

        # Invalidate
        await cache.invalidate_key(sample_api_keys[0].id)

        # Verify it's gone
        key = await cache.get_by_id(sample_api_keys[0].id)
        assert key is None

        # Verify also gone from prefix index
        key = await cache.get_by_prefix(sample_api_keys[0].key_prefix)
        assert key is None

    async def test_hit_rate_calculation(self, redis_client, cache_namespace, mock_repository):
        """Should calculate hit rate correctly."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        # Generate hits and misses
        await cache.get_by_prefix("sk_live_abc1")  # hit
        await cache.get_by_prefix("sk_live_abc1")  # hit
        await cache.get_by_prefix("sk_live_abc1")  # hit
        await cache.get_by_prefix("sk_live_nonexistent")  # miss

        stats = cache.get_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 1
        assert stats["hit_rate"] == "75.00%"

    async def test_stats_active_key_count(self, redis_client, cache_namespace, mock_repository):
        """Should correctly count active keys."""
        cache = ApiKeyCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        stats = cache.get_stats()
        assert stats["total_keys"] == 3
        assert stats["active_keys"] == 2  # One is inactive
