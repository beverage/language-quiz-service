"""Integration tests for the ApiKeyRepository."""

import uuid

import pytest

from src.core.exceptions import RepositoryError
from src.repositories.api_keys_repository import ApiKeyRepository
from src.schemas.api_keys import ApiKeyCreate, ApiKeyUpdate


@pytest.fixture
def api_keys_repository(test_supabase_client):
    """Fixture to provide an ApiKeyRepository instance."""
    return ApiKeyRepository(test_supabase_client)


@pytest.mark.asyncio
@pytest.mark.integration
class TestApiKeyRepository:
    """Test suite for ApiKeyRepository integration tests."""

    @pytest.fixture(autouse=True)
    async def setup(self, api_keys_repository: ApiKeyRepository):
        """Initializes the repository for each test."""
        self.repository = api_keys_repository

    async def test_create_api_key_success(self):
        """Test creating an API key successfully."""
        key_name = f"test-key-{uuid.uuid4()}"
        key_data = ApiKeyCreate(name=key_name, permissions_scope=["read"])
        key_hash = f"testhash-{uuid.uuid4()}"
        key_prefix = f"test_prefix_{uuid.uuid4()}"

        created_key = await self.repository.create_api_key(
            key_data, key_hash, key_prefix
        )

        assert created_key is not None
        assert created_key.name == key_name
        assert created_key.key_hash == key_hash
        assert created_key.key_prefix == key_prefix
        assert created_key.is_active is True

    async def test_get_api_key_by_id_success(self):
        """Test retrieving an API key by its ID."""
        key_name = f"get-by-id-{uuid.uuid4()}"
        key_data = ApiKeyCreate(name=key_name, permissions_scope=["read"])
        created_key = await self.repository.create_api_key(
            key_data, f"hash-{uuid.uuid4()}", f"prefix-{uuid.uuid4()}"
        )

        fetched_key = await self.repository.get_api_key(created_key.id)

        assert fetched_key is not None
        assert fetched_key.id == created_key.id
        assert fetched_key.name == key_name

    async def test_get_api_key_by_id_not_found(self):
        """Test that None is returned for a non-existent API key ID."""
        non_existent_id = uuid.uuid4()
        fetched_key = await self.repository.get_api_key(non_existent_id)
        assert fetched_key is None

    async def test_get_api_key_by_prefix_success(self):
        """Test retrieving an API key by its prefix."""
        prefix = f"test_prefix_{uuid.uuid4()}"
        key_data = ApiKeyCreate(
            name=f"prefix-test-{uuid.uuid4()}", permissions_scope=["read"]
        )
        await self.repository.create_api_key(key_data, f"hash-{uuid.uuid4()}", prefix)

        fetched_key = await self.repository.get_api_key_by_prefix(prefix)

        assert fetched_key is not None
        assert fetched_key.key_prefix == prefix

    async def test_get_api_key_by_prefix_not_found(self):
        """Test that None is returned for a non-existent prefix."""
        fetched_key = await self.repository.get_api_key_by_prefix("non_existent_prefix")
        assert fetched_key is None

    async def test_update_api_key_success(self):
        """Test updating an API key's details."""
        key_name = f"update-test-{uuid.uuid4()}"
        key_data = ApiKeyCreate(name=key_name, permissions_scope=["read"])
        created_key = await self.repository.create_api_key(
            key_data, f"hash-{uuid.uuid4()}", f"prefix-{uuid.uuid4()}"
        )

        update_data = ApiKeyUpdate(
            name="updated-name", description="updated description"
        )
        updated_key = await self.repository.update_api_key(created_key.id, update_data)

        assert updated_key is not None
        assert updated_key.name == "updated-name"
        assert updated_key.description == "updated description"

    async def test_update_api_key_not_found(self):
        """Test that updating a non-existent key returns None."""
        non_existent_id = uuid.uuid4()
        update_data = ApiKeyUpdate(name="new-name")
        result = await self.repository.update_api_key(non_existent_id, update_data)
        assert result is None

    async def test_delete_api_key_success(self):
        """Test successfully deleting an API key."""
        key_data = ApiKeyCreate(
            name=f"delete-test-{uuid.uuid4()}", permissions_scope=["read"]
        )
        created_key = await self.repository.create_api_key(
            key_data, f"hash-{uuid.uuid4()}", f"prefix-{uuid.uuid4()}"
        )

        deleted_key = await self.repository.delete_api_key(created_key.id)
        assert deleted_key is True

        # Verify it's gone
        fetched_key = await self.repository.get_api_key(created_key.id)
        assert fetched_key.is_active is False

    async def test_delete_api_key_not_found(self):
        """Test that deleting a non-existent key returns None."""
        non_existent_id = uuid.uuid4()
        result = await self.repository.delete_api_key(non_existent_id)
        assert result is False

    async def test_increment_usage_success(self):
        """Test incrementing the usage count for an API key."""
        key_data = ApiKeyCreate(
            name=f"usage-test-{uuid.uuid4()}", permissions_scope=["read"]
        )
        created_key = await self.repository.create_api_key(
            key_data, f"hash-{uuid.uuid4()}", f"prefix-{uuid.uuid4()}"
        )

        assert created_key.usage_count == 0

        await self.repository.increment_usage(created_key.id)

        updated_key = await self.repository.get_api_key(created_key.id)
        assert updated_key.usage_count == 1
        assert updated_key.last_used_at is not None
