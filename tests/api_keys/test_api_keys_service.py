"""Integration tests for the API Key service."""

import uuid
from datetime import datetime

import pytest

from src.core.exceptions import NotFoundError
from src.repositories.api_keys_repository import ApiKeyRepository
from src.schemas.api_keys import ApiKeyCreate, ApiKeyUpdate
from src.services.api_key_service import ApiKeyService


@pytest.fixture
async def api_keys_repository(test_supabase_client):
    """Fixture to provide an ApiKeyRepository instance for integration tests."""
    return ApiKeyRepository(test_supabase_client)


@pytest.fixture
async def api_key_service(api_keys_repository):
    """Fixture to provide an ApiKeyService instance for integration tests."""
    return ApiKeyService(api_key_repository=api_keys_repository)


@pytest.mark.asyncio
@pytest.mark.integration
class TestApiKeyServiceIntegration:
    """Test suite for ApiKeyService integration tests."""

    async def test_create_and_get_api_key(self, api_key_service: ApiKeyService):
        """Test creating a new API key and then retrieving it."""
        create_data = ApiKeyCreate(
            name=f"integration-test-key-{uuid.uuid4()}",
            permissions_scope=["read", "write"],
        )

        # 1. Create the key
        created_key_with_plain_text = await api_key_service.create_api_key(create_data)
        assert created_key_with_plain_text is not None
        assert created_key_with_plain_text.api_key.startswith("sk_live_")
        created_info = created_key_with_plain_text.key_info

        # 2. Get the key by ID
        fetched_key = await api_key_service.get_api_key(created_info.id)
        assert fetched_key is not None
        assert fetched_key.id == created_info.id
        assert fetched_key.name == create_data.name
        assert fetched_key.permissions_scope == ["read", "write"]

    async def test_get_api_key_not_found(self, api_key_service: ApiKeyService):
        """Test that getting a non-existent API key raises NotFoundError."""
        non_existent_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await api_key_service.get_api_key(non_existent_id)

    async def test_update_api_key(
        self, api_key_service: ApiKeyService, api_keys_repository: ApiKeyRepository
    ):
        """Test updating an API key's properties."""
        # First, create a key to update
        create_data = ApiKeyCreate(
            name=f"update-test-{uuid.uuid4()}", permissions_scope=["read"]
        )
        created_key_info = (await api_key_service.create_api_key(create_data)).key_info

        # Now, update it
        update_data = ApiKeyUpdate(
            name="new-updated-name", description="A new description"
        )
        updated_key = await api_key_service.update_api_key(
            created_key_info.id, update_data
        )

        assert updated_key is not None
        assert updated_key.name == "new-updated-name"
        assert updated_key.description == "A new description"

        # Verify in DB
        db_key = await api_keys_repository.get_api_key(created_key_info.id)
        assert db_key.name == "new-updated-name"

    async def test_revoke_api_key(
        self, api_key_service: ApiKeyService, api_keys_repository: ApiKeyRepository
    ):
        """Test revoking an API key."""
        # First, create a key to revoke
        create_data = ApiKeyCreate(
            name=f"revoke-test-{uuid.uuid4()}", permissions_scope=["read"]
        )
        created_key_info = (await api_key_service.create_api_key(create_data)).key_info
        assert created_key_info.is_active is True

        # Revoke it
        result = await api_key_service.revoke_api_key(created_key_info.id)
        assert result is True

        # Verify it's inactive by trying to fetch it via the service, which should fail
        with pytest.raises(NotFoundError):
            await api_key_service.get_api_key(created_key_info.id)

    async def test_authenticate_api_key(self, api_key_service: ApiKeyService):
        """Test the full authentication flow for a valid API key."""
        # 1. Create a key
        create_data = ApiKeyCreate(
            name=f"auth-test-{uuid.uuid4()}", permissions_scope=["read"]
        )
        created_key_with_plain_text = await api_key_service.create_api_key(create_data)
        plain_text_key = created_key_with_plain_text.api_key
        key_id = created_key_with_plain_text.key_info.id

        # 2. Authenticate with the plain text key
        authenticated_key = await api_key_service.authenticate_api_key(plain_text_key)

        assert authenticated_key is not None
        assert authenticated_key.id == key_id

    async def test_authentication_fails_for_invalid_key(
        self, api_key_service: ApiKeyService
    ):
        """Test that authentication returns None for an invalid or non-existent key."""
        result = await api_key_service.authenticate_api_key(
            "test_key_invalid_not_a_real_key_12345678"
        )
        assert result is None
