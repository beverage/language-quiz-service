"""
API tests for API key management endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.schemas.api_keys import (
    ApiKeyResponse,
    ApiKeyWithPlainText,
    ApiKeyStats,
)


class TestApiKeysApi:
    """Test suite for API key management endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        return TestClient(app)

    @pytest.fixture
    def mock_admin_key_info(self):
        """Mock admin API key info for authorization."""
        return {
            "id": str(uuid4()),
            "key_prefix": "sk_live_admin",
            "name": "Admin Key",
            "description": "Admin API key",
            "client_name": "admin-client",
            "is_active": True,
            "permissions_scope": ["admin"],
            "created_at": datetime.now().isoformat(),
            "last_used_at": None,
            "usage_count": 0,
            "rate_limit_rpm": 1000,
            "allowed_ips": ["127.0.0.1"],
        }

    @pytest.fixture
    def sample_api_key_response(self):
        """Sample API key response for testing."""
        return ApiKeyResponse(
            id=uuid4(),
            key_prefix="sk_live_test",
            name="Test API Key",
            description="A test API key",
            client_name="test-client",
            is_active=True,
            permissions_scope=["read", "write"],
            created_at=datetime.now(),
            last_used_at=None,
            usage_count=0,
            rate_limit_rpm=100,
            allowed_ips=["127.0.0.1"],
        )

    @pytest.fixture
    def sample_api_key_with_plaintext(self):
        """Sample API key with plaintext for testing."""
        return ApiKeyWithPlainText(
            api_key="sk_live_" + "a" * 56,  # Full plaintext API key
            key_info=ApiKeyResponse(
                id=uuid4(),
                key_prefix="sk_live_test",
                name="Test API Key",
                description="A test API key",
                client_name="test-client",
                is_active=True,
                permissions_scope=["read", "write"],
                created_at=datetime.now(),
                last_used_at=None,
                usage_count=0,
                rate_limit_rpm=100,
                allowed_ips=["127.0.0.1"],
            ),
        )

    @pytest.fixture
    def sample_api_key_create(self):
        """Sample API key creation data."""
        return {
            "name": "Test API Key",
            "description": "A test API key",
            "client_name": "test-client",
            "permissions_scope": ["read", "write"],
            "rate_limit_rpm": 100,
            "allowed_ips": ["127.0.0.1"],
        }

    def _mock_auth_middleware(self, mock_key_info):
        """Helper to mock the authentication middleware for isolated testing."""

        async def mock_dispatch(request, call_next):
            # Mock the request state with API key info
            request.state.api_key_info = mock_key_info
            request.state.client_ip = "127.0.0.1"
            return await call_next(request)

        return patch(
            "src.core.auth.ApiKeyAuthMiddleware.dispatch", side_effect=mock_dispatch
        )

    def test_create_api_key_success(
        self,
        client,
        mock_admin_key_info,
        sample_api_key_create,
        sample_api_key_with_plaintext,
    ):
        """Test successful API key creation."""
        with self._mock_auth_middleware(mock_admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service:
                mock_service_instance = AsyncMock()
                mock_service.return_value = mock_service_instance
                mock_service_instance.create_api_key.return_value = (
                    sample_api_key_with_plaintext
                )

                response = client.post(
                    "/api-keys/",
                    json=sample_api_key_create,
                    headers={"X-API-Key": "sk_live_admin123"},
                )

                assert (
                    response.status_code == status.HTTP_200_OK
                )  # API endpoint returns 200, not 201
                data = response.json()
                assert data["api_key"].startswith("sk_live_")
                assert data["key_info"]["name"] == "Test API Key"

    def test_get_current_key_info_success(self, client, mock_admin_key_info):
        """Test retrieving current API key info."""
        with self._mock_auth_middleware(mock_admin_key_info):
            response = client.get(
                "/api-keys/current", headers={"X-API-Key": "sk_live_admin123"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Admin Key"
            assert data["key_prefix"] == "sk_live_admin"

    def test_get_api_key_stats_success(self, client, mock_admin_key_info):
        """Test retrieving API key statistics."""
        with self._mock_auth_middleware(mock_admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service:
                mock_service_instance = AsyncMock()
                mock_service.return_value = mock_service_instance
                mock_service_instance.get_api_key_stats.return_value = ApiKeyStats(
                    total_keys=10,
                    active_keys=8,
                    inactive_keys=2,
                    total_requests=1000,
                    requests_last_24h=50,
                    most_active_key="sk_live_test",
                )

                response = client.get(
                    "/api-keys/stats", headers={"X-API-Key": "sk_live_admin123"}
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["total_keys"] == 10
                assert data["active_keys"] == 8
                assert data["total_requests"] == 1000
                assert data["most_active_key"] == "sk_live_test"

    @pytest.mark.parametrize(
        "api_key,expected",
        [
            ("sk_live_" + "a" * 56, True),
            ("sk_test_" + "a" * 56, False),  # Only sk_live_ is valid
            ("invalid_key", False),
            ("sk_live_" + "a" * 20, False),  # Too short
        ],
    )
    async def test_validate_api_key_format(self, api_key, expected):
        """Test API key format validation."""
        from src.services.api_key_service import ApiKeyService

        service = ApiKeyService()
        is_valid, error_message = await service.verify_api_key_format(api_key)
        assert is_valid == expected
