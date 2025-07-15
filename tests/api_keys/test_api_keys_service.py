"""
Tests for the API key service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from src.services.api_key_service import ApiKeyService
from src.schemas.api_keys import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyWithPlainText,
    ApiKeyStats,
    ApiKey,
)


class TestApiKeyService:
    """Test suite for ApiKeyService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock API key repository."""
        mock_repo = Mock()
        mock_repo.create_api_key = AsyncMock()
        mock_repo.get_api_key = AsyncMock()
        mock_repo.get_api_key_by_hash = AsyncMock()
        mock_repo.get_api_key_by_prefix = AsyncMock()
        mock_repo.get_all_api_keys = AsyncMock()
        mock_repo.update_api_key = AsyncMock()
        mock_repo.delete_api_key = AsyncMock()
        mock_repo.increment_usage = AsyncMock()
        mock_repo.get_api_key_stats = AsyncMock()
        mock_repo.find_keys_by_name = AsyncMock()
        return mock_repo

    @pytest.fixture
    def service(self, mock_repository):
        """Create an API key service with mocked repository."""
        return ApiKeyService(mock_repository)

    @pytest.fixture
    def sample_api_key(self):
        """Create a sample API key for testing."""
        return ApiKey(
            id=uuid4(),
            key_hash="$2b$12$sample_hash",
            key_prefix="sk_live_abcd",
            name="Test Key",
            description="Test description",
            client_name="test-client",
            is_active=True,
            permissions_scope=["read", "write"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_used_at=None,
            usage_count=0,
            rate_limit_rpm=100,
            allowed_ips=["192.168.1.0/24"],
        )

    @pytest.fixture
    def sample_api_key_create(self):
        """Create a sample API key creation request."""
        return ApiKeyCreate(
            name="Test Key",
            description="Test description",
            client_name="test-client",
            permissions_scope=["read", "write"],
            rate_limit_rpm=100,
            allowed_ips=["192.168.1.0/24"],
        )

    @pytest.mark.asyncio
    async def test_create_api_key_success(
        self, service, mock_repository, sample_api_key_create, sample_api_key
    ):
        """Test successful API key creation."""
        # Mock repository response
        mock_repository.create_api_key.return_value = sample_api_key

        # Mock key generation
        with patch(
            "src.services.api_key_service.generate_api_key"
        ) as mock_generate, patch(
            "src.services.api_key_service.hash_api_key"
        ) as mock_hash:
            mock_generate.return_value = ("sk_live_test123", "sk_live_test")
            mock_hash.return_value = "hashed_key"

            result = await service.create_api_key(sample_api_key_create)

            # Verify the result
            assert isinstance(result, ApiKeyWithPlainText)
            assert result.api_key == "sk_live_test123"
            assert result.key_info.name == "Test Key"
            assert result.key_info.permissions_scope == ["read", "write"]

            # Verify repository was called correctly
            mock_repository.create_api_key.assert_called_once_with(
                sample_api_key_create, "hashed_key", "sk_live_test"
            )

    @pytest.mark.asyncio
    async def test_get_api_key_success(self, service, mock_repository, sample_api_key):
        """Test successful API key retrieval."""
        mock_repository.get_api_key.return_value = sample_api_key

        result = await service.get_api_key(sample_api_key.id)

        assert isinstance(result, ApiKeyResponse)
        assert result.name == "Test Key"
        assert result.id == sample_api_key.id

        mock_repository.get_api_key.assert_called_once_with(sample_api_key.id)

    @pytest.mark.asyncio
    async def test_get_api_key_not_found(self, service, mock_repository):
        """Test API key retrieval when key doesn't exist."""
        mock_repository.get_api_key.return_value = None

        result = await service.get_api_key(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_api_keys(self, service, mock_repository, sample_api_key):
        """Test getting all API keys."""
        mock_repository.get_all_api_keys.return_value = [sample_api_key]

        result = await service.get_all_api_keys(limit=50, include_inactive=True)

        assert len(result) == 1
        assert isinstance(result[0], ApiKeyResponse)
        assert result[0].name == "Test Key"

        mock_repository.get_all_api_keys.assert_called_once_with(50, True)

    @pytest.mark.asyncio
    async def test_update_api_key_success(
        self, service, mock_repository, sample_api_key
    ):
        """Test successful API key update."""
        updated_key = sample_api_key.model_copy(deep=True)
        updated_key.name = "Updated Key"
        mock_repository.update_api_key.return_value = updated_key

        update_data = ApiKeyUpdate(name="Updated Key")
        result = await service.update_api_key(sample_api_key.id, update_data)

        assert isinstance(result, ApiKeyResponse)
        assert result.name == "Updated Key"

        mock_repository.update_api_key.assert_called_once_with(
            sample_api_key.id, update_data
        )

    @pytest.mark.asyncio
    async def test_update_api_key_not_found(self, service, mock_repository):
        """Test API key update when key doesn't exist."""
        mock_repository.update_api_key.return_value = None

        update_data = ApiKeyUpdate(name="Updated Key")
        result = await service.update_api_key(uuid4(), update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, service, mock_repository):
        """Test successful API key revocation."""
        mock_repository.delete_api_key.return_value = True

        result = await service.revoke_api_key(uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_api_key_not_found(self, service, mock_repository):
        """Test API key revocation when key doesn't exist."""
        mock_repository.delete_api_key.return_value = False

        result = await service.revoke_api_key(uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_authenticate_api_key_success(
        self, service, mock_repository, sample_api_key
    ):
        """Test successful API key authentication."""
        mock_repository.get_api_key_by_prefix.return_value = sample_api_key
        mock_repository.increment_usage.return_value = True

        with patch("src.services.api_key_service.verify_api_key") as mock_verify, patch(
            "src.services.api_key_service.check_ip_allowed"
        ) as mock_ip_check:
            mock_verify.return_value = True
            mock_ip_check.return_value = True

            result = await service.authenticate_api_key(
                "sk_live_test123", "192.168.1.1"
            )

            assert isinstance(result, ApiKeyResponse)
            assert result.name == "Test Key"

            mock_repository.get_api_key_by_prefix.assert_called_once_with(
                "sk_live_test123"
            )
            mock_repository.increment_usage.assert_called_once_with(sample_api_key.id)

    @pytest.mark.asyncio
    async def test_authenticate_api_key_invalid_prefix(self, service, mock_repository):
        """Test authentication with invalid API key prefix."""
        result = await service.authenticate_api_key("invalid_key", "192.168.1.1")

        assert result is None
        mock_repository.get_api_key_by_prefix.assert_not_called()

    @pytest.mark.asyncio
    async def test_authenticate_api_key_not_found(self, service, mock_repository):
        """Test authentication when API key doesn't exist."""
        mock_repository.get_api_key_by_prefix.return_value = None

        result = await service.authenticate_api_key("sk_live_test123", "192.168.1.1")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_api_key_inactive(
        self, service, mock_repository, sample_api_key
    ):
        """Test authentication with inactive API key."""
        inactive_key = sample_api_key.model_copy(deep=True)
        inactive_key.is_active = False
        mock_repository.get_api_key_by_prefix.return_value = inactive_key

        result = await service.authenticate_api_key("sk_live_test123", "192.168.1.1")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_api_key_ip_blocked(
        self, service, mock_repository, sample_api_key
    ):
        """Test authentication with blocked IP."""
        mock_repository.get_api_key_by_prefix.return_value = sample_api_key

        with patch("src.services.api_key_service.verify_api_key") as mock_verify, patch(
            "src.services.api_key_service.check_ip_allowed"
        ) as mock_ip_check:
            mock_verify.return_value = True
            mock_ip_check.return_value = False

            result = await service.authenticate_api_key("sk_live_test123", "10.0.0.1")

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_api_key_exception(self, service, mock_repository):
        """Test authentication with database exception."""
        mock_repository.get_api_key_by_prefix.side_effect = Exception("Database error")

        result = await service.authenticate_api_key("sk_live_test123", "192.168.1.1")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_api_key_verification_failed(
        self, service, mock_repository, sample_api_key
    ):
        """Test authentication when API key verification fails."""
        mock_repository.get_api_key_by_prefix.return_value = sample_api_key

        with patch("src.services.api_key_service.verify_api_key") as mock_verify:
            mock_verify.return_value = False

            result = await service.authenticate_api_key(
                "sk_live_test123", "192.168.1.1"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_format_valid(self, service):
        """Test API key format validation with valid key."""
        valid_key = "sk_live_" + "a" * 56

        is_valid, error_message = await service.verify_api_key_format(valid_key)

        assert is_valid is True
        assert error_message is None

    @pytest.mark.asyncio
    async def test_verify_api_key_format_invalid_prefix(self, service):
        """Test API key format validation with invalid prefix."""
        invalid_key = "invalid_prefix" + "a" * 56

        is_valid, error_message = await service.verify_api_key_format(invalid_key)

        assert is_valid is False
        assert "must start with 'sk_live_'" in error_message

    @pytest.mark.asyncio
    async def test_verify_api_key_format_invalid_length(self, service):
        """Test API key format validation with invalid length."""
        invalid_key = "sk_live_short"

        is_valid, error_message = await service.verify_api_key_format(invalid_key)

        assert is_valid is False
        assert "invalid length" in error_message

    @pytest.mark.asyncio
    async def test_verify_api_key_format_invalid_characters(self, service):
        """Test API key format validation with invalid characters."""
        invalid_key = "sk_live_" + "a" * 55 + "!"

        is_valid, error_message = await service.verify_api_key_format(invalid_key)

        assert is_valid is False
        assert "invalid characters" in error_message

    @pytest.mark.asyncio
    async def test_verify_api_key_format_empty(self, service):
        """Test API key format validation with empty key."""
        is_valid, error_message = await service.verify_api_key_format("")

        assert is_valid is False
        assert "required" in error_message

    @pytest.mark.asyncio
    async def test_get_api_key_stats(self, service, mock_repository):
        """Test getting API key statistics."""
        stats = ApiKeyStats(
            total_keys=10,
            active_keys=8,
            inactive_keys=2,
            total_requests=1000,
            requests_last_24h=50,
            most_active_key="sk_live_abcd",
        )
        mock_repository.get_api_key_stats.return_value = stats

        result = await service.get_api_key_stats()

        assert isinstance(result, ApiKeyStats)
        assert result.total_keys == 10
        assert result.active_keys == 8
        assert result.most_active_key == "sk_live_abcd"

    @pytest.mark.asyncio
    async def test_find_api_keys_by_name(
        self, service, mock_repository, sample_api_key
    ):
        """Test finding API keys by name pattern."""
        mock_repository.find_keys_by_name.return_value = [sample_api_key]

        result = await service.find_api_keys_by_name("Test")

        assert len(result) == 1
        assert isinstance(result[0], ApiKeyResponse)
        assert result[0].name == "Test Key"

        mock_repository.find_keys_by_name.assert_called_once_with("Test")

    @pytest.mark.asyncio
    async def test_check_rate_limit(self, service, sample_api_key):
        """Test rate limit checking (currently always returns True)."""
        api_key_response = ApiKeyResponse.model_validate(sample_api_key.model_dump())

        result = await service.check_rate_limit(api_key_response)

        assert result is True

    @pytest.mark.asyncio
    async def test_is_api_key_expired(self, service, sample_api_key):
        """Test API key expiration checking (currently always returns False)."""
        api_key_response = ApiKeyResponse.model_validate(sample_api_key.model_dump())

        result = await service.is_api_key_expired(api_key_response)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_permissions(self, service, sample_api_key):
        """Test getting API key permissions."""
        api_key_response = ApiKeyResponse.model_validate(sample_api_key.model_dump())

        result = await service.get_permissions(api_key_response)

        assert result == ["read", "write"]

    @pytest.mark.asyncio
    async def test_has_permission_true(self, service, sample_api_key):
        """Test checking if API key has a specific permission (true case)."""
        api_key_response = ApiKeyResponse.model_validate(sample_api_key.model_dump())

        result = await service.has_permission(api_key_response, "read")

        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_false(self, service, sample_api_key):
        """Test checking if API key has a specific permission (false case)."""
        api_key_response = ApiKeyResponse.model_validate(sample_api_key.model_dump())

        result = await service.has_permission(api_key_response, "admin")

        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission_admin_override(self, service, sample_api_key):
        """Test that admin permission grants access to any other permission."""
        admin_key = sample_api_key.model_copy(deep=True)
        admin_key.permissions_scope = ["admin"]
        api_key_response = ApiKeyResponse.model_validate(admin_key.model_dump())

        result = await service.has_permission(api_key_response, "write")

        assert result is True

    @pytest.mark.asyncio
    async def test_service_without_injected_repository(self):
        """Test that the service can create its own repository when none is injected."""
        service = ApiKeyService()

        # This should not raise an exception
        assert service.api_key_repository is None

        # The repository should be created lazily when needed
        with patch("src.services.api_key_service.get_supabase_client") as mock_client:
            mock_client.return_value = Mock()

            repo = await service._get_api_key_repository()

            assert repo is not None
            assert service.api_key_repository is not None
