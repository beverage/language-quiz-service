"""Clean API contract tests for API keys endpoints.

These tests focus on HTTP request/response behavior, parameter handling,
and API contract validation without complex dependency injection.
"""

from contextlib import contextmanager
from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.schemas.api_keys import (
    ApiKeyResponse,
    ApiKeyStats,
    ApiKeyWithPlainText,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Headers for admin API key authentication."""
    return {"X-API-Key": "sk_live_admin123"}


@pytest.fixture
def read_headers():
    """Headers for read-only API key authentication."""
    return {"X-API-Key": "sk_live_read123"}


@pytest.fixture
def sample_api_key_response():
    """Sample API key response for testing."""
    return ApiKeyResponse(
        id=uuid4(),
        key_prefix="sk_live_test",
        name="Test API Key",
        description="A test API key",
        client_name="test-client",
        is_active=True,
        permissions_scope=["read", "write"],
        created_at=datetime.now(UTC),
        last_used_at=None,
        usage_count=0,
        rate_limit_rpm=100,
        allowed_ips=["127.0.0.1"],
    )


@pytest.fixture
def sample_api_key_with_plaintext(sample_api_key_response):
    """Sample API key with plaintext for testing."""
    return ApiKeyWithPlainText(
        api_key="sk_live_" + "a" * 56,  # Full plaintext API key
        key_info=sample_api_key_response,
    )


@pytest.fixture
def sample_api_key_stats():
    """Sample API key statistics for testing."""
    return ApiKeyStats(
        total_keys=10,
        active_keys=8,
        inactive_keys=2,
        total_requests=1000,
        requests_last_24h=50,
        most_active_key="sk_live_test",
    )


@pytest.fixture
def admin_key_info():
    """Mock admin API key info for authorization."""
    return {
        "id": str(uuid4()),
        "key_prefix": "sk_live_admin",
        "name": "Admin Key",
        "description": "Admin API key",
        "client_name": "admin-client",
        "is_active": True,
        "permissions_scope": ["admin"],
        "created_at": datetime.now(UTC).isoformat(),
        "last_used_at": None,
        "usage_count": 0,
        "rate_limit_rpm": 1000,
        "allowed_ips": ["127.0.0.1"],
    }


@pytest.fixture
def read_key_info():
    """Mock read-only API key info for authorization."""
    return {
        "id": str(uuid4()),
        "key_prefix": "sk_live_read",
        "name": "Read Key",
        "description": "Read-only API key",
        "client_name": "read-client",
        "is_active": True,
        "permissions_scope": ["read"],
        "created_at": datetime.now(UTC).isoformat(),
        "last_used_at": None,
        "usage_count": 0,
        "rate_limit_rpm": 100,
        "allowed_ips": ["127.0.0.1"],
    }


@contextmanager
def _mock_auth_middleware(mock_key_info):
    """Helper to mock authentication middleware with specific key info."""

    async def mock_dispatch(request, call_next):
        request.state.api_key_info = mock_key_info
        request.state.client_ip = "127.0.0.1"
        return await call_next(request)

    with patch(
        "src.core.auth.ApiKeyAuthMiddleware.dispatch", side_effect=mock_dispatch
    ):
        yield


class TestApiKeysAPIContract:
    """Test API keys endpoint HTTP contracts and behavior."""

    def test_create_api_key_success(
        self,
        client: TestClient,
        admin_headers,
        admin_key_info,
        sample_api_key_with_plaintext,
    ):
        """Test successful API key creation."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.create_api_key.return_value = sample_api_key_with_plaintext

                create_data = {
                    "name": "Test API Key",
                    "description": "A test API key",
                    "client_name": "test-client",
                    "permissions_scope": ["read", "write"],
                    "rate_limit_rpm": 100,
                    "allowed_ips": ["127.0.0.1"],
                }

                response = client.post(
                    "/api-keys/", json=create_data, headers=admin_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["api_key"].startswith("sk_live_")
                assert data["key_info"]["name"] == "Test API Key"
                assert data["key_info"]["permissions_scope"] == ["read", "write"]

    @pytest.mark.skip(
        reason="Auth permission testing - belongs in e2e/security test suite"
    )
    def test_create_api_key_insufficient_permissions(
        self, client: TestClient, read_headers, read_key_info
    ):
        """Test API key creation with insufficient permissions."""
        with _mock_auth_middleware(read_key_info):
            with patch("src.clients.supabase.get_supabase_client"):
                create_data = {
                    "name": "Test API Key",
                    "permissions_scope": ["read"],
                }

                response = client.post(
                    "/api-keys/", json=create_data, headers=read_headers
                )

                assert response.status_code == 403
                data = response.json()
                assert "admin permission required" in data["message"].lower()

    def test_list_api_keys_success(
        self, client: TestClient, admin_headers, admin_key_info, sample_api_key_response
    ):
        """Test successful API keys listing."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_all_api_keys.return_value = [sample_api_key_response]

                response = client.get("/api-keys/", headers=admin_headers)

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["name"] == "Test API Key"
                assert data[0]["key_prefix"] == "sk_live_test"

    def test_list_api_keys_with_parameters(
        self, client: TestClient, admin_headers, admin_key_info
    ):
        """Test API keys listing with query parameters."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_all_api_keys.return_value = []

                response = client.get(
                    "/api-keys/?limit=50&include_inactive=true", headers=admin_headers
                )

                assert response.status_code == 200
                # Verify service was called with correct parameters
                mock_service.get_all_api_keys.assert_called_once_with(50, True)

    def test_get_api_key_stats_success(
        self, client: TestClient, admin_headers, admin_key_info, sample_api_key_stats
    ):
        """Test successful API key statistics retrieval."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_api_key_stats.return_value = sample_api_key_stats

                response = client.get("/api-keys/stats", headers=admin_headers)

                assert response.status_code == 200
                data = response.json()
                assert data["total_keys"] == 10
                assert data["active_keys"] == 8
                assert data["total_requests"] == 1000
                assert data["most_active_key"] == "sk_live_test"

    def test_get_current_key_info_success(
        self, client: TestClient, admin_headers, admin_key_info
    ):
        """Test successful current key info retrieval."""
        with _mock_auth_middleware(admin_key_info):
            response = client.get("/api-keys/current", headers=admin_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Admin Key"
            assert data["key_prefix"] == "sk_live_admin"
            assert data["permissions_scope"] == ["admin"]

    def test_get_api_key_by_id_success(
        self, client: TestClient, admin_headers, admin_key_info, sample_api_key_response
    ):
        """Test successful API key retrieval by ID."""
        key_id = sample_api_key_response.id

        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_api_key.return_value = sample_api_key_response

                response = client.get(f"/api-keys/{key_id}", headers=admin_headers)

                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Test API Key"
                assert data["id"] == str(key_id)

    def test_get_api_key_by_id_not_found(
        self, client: TestClient, admin_headers, admin_key_info
    ):
        """Test API key retrieval for non-existent key."""
        key_id = uuid4()

        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_api_key.return_value = None

                response = client.get(f"/api-keys/{key_id}", headers=admin_headers)

                assert response.status_code == 404
                data = response.json()
                # API uses custom error format, could be "detail" or "message"
                error_message = data.get("detail", data.get("message", "")).lower()
                assert "not found" in error_message

    def test_update_api_key_success(
        self, client: TestClient, admin_headers, admin_key_info, sample_api_key_response
    ):
        """Test successful API key update."""
        key_id = sample_api_key_response.id
        updated_key = sample_api_key_response.model_copy(deep=True)
        updated_key.name = "Updated API Key"

        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.update_api_key.return_value = updated_key

                update_data = {
                    "name": "Updated API Key",
                    "description": "Updated description",
                }

                response = client.put(
                    f"/api-keys/{key_id}", json=update_data, headers=admin_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Updated API Key"

    def test_revoke_api_key_success(
        self, client: TestClient, admin_headers, admin_key_info
    ):
        """Test successful API key revocation."""
        key_id = uuid4()

        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.revoke_api_key.return_value = True

                response = client.delete(f"/api-keys/{key_id}", headers=admin_headers)

                assert response.status_code == 200
                data = response.json()
                assert "revoked successfully" in data["message"]

    def test_search_api_keys_success(
        self, client: TestClient, admin_headers, admin_key_info, sample_api_key_response
    ):
        """Test successful API key search."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.find_api_keys_by_name.return_value = [
                    sample_api_key_response
                ]

                response = client.get(
                    "/api-keys/search?name=test", headers=admin_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["name"] == "Test API Key"


class TestApiKeysAPIParameterHandling:
    """Test parameter validation and handling in API keys API."""

    def test_create_api_key_validation(
        self, client: TestClient, admin_headers, admin_key_info
    ):
        """Test API key creation parameter validation."""
        with _mock_auth_middleware(admin_key_info):
            # Missing required fields
            response = client.post("/api-keys/", json={}, headers=admin_headers)

            assert response.status_code == 422  # Validation error

    def test_list_api_keys_parameter_validation(
        self, client: TestClient, admin_headers, admin_key_info
    ):
        """Test list API keys parameter validation."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_all_api_keys.return_value = []

                # Test parameter bounds
                response = client.get(
                    "/api-keys/?limit=1500",  # Over max limit
                    headers=admin_headers,
                )

                assert response.status_code == 422  # Validation error

    def test_search_missing_name_parameter(
        self, client: TestClient, admin_headers, admin_key_info
    ):
        """Test search API keys with missing name parameter."""
        with _mock_auth_middleware(admin_key_info):
            response = client.get("/api-keys/search", headers=admin_headers)

            assert response.status_code == 422  # Missing required parameter


class TestApiKeysAPIResponseFormats:
    """Test response formats and schemas."""

    def test_api_key_response_schema(
        self, client: TestClient, admin_headers, admin_key_info, sample_api_key_response
    ):
        """Test API key response contains all required fields."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_all_api_keys.return_value = [sample_api_key_response]

                response = client.get("/api-keys/", headers=admin_headers)

                assert response.status_code == 200
                data = response.json()[0]

                # Required fields
                required_fields = [
                    "id",
                    "key_prefix",
                    "name",
                    "is_active",
                    "permissions_scope",
                    "created_at",
                    "rate_limit_rpm",
                ]
                for field in required_fields:
                    assert field in data

    def test_api_key_with_plaintext_schema(
        self,
        client: TestClient,
        admin_headers,
        admin_key_info,
        sample_api_key_with_plaintext,
    ):
        """Test API key with plaintext response schema."""
        with _mock_auth_middleware(admin_key_info):
            with patch("src.api.api_keys.ApiKeyService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.create_api_key.return_value = sample_api_key_with_plaintext

                create_data = {
                    "name": "Test API Key",
                    "permissions_scope": ["read"],
                }

                response = client.post(
                    "/api-keys/", json=create_data, headers=admin_headers
                )

                assert response.status_code == 200
                data = response.json()

                # Should have both api_key and key_info
                assert "api_key" in data
                assert "key_info" in data
                assert data["api_key"].startswith("sk_live_")

    @pytest.mark.skip(
        reason="Auth permission testing - belongs in e2e/security test suite"
    )
    def test_error_response_format(
        self, client: TestClient, read_headers, read_key_info
    ):
        """Test error response format consistency."""
        with _mock_auth_middleware(read_key_info):
            with patch("src.clients.supabase.get_supabase_client"):
                response = client.post(
                    "/api-keys/", json={"name": "Test"}, headers=read_headers
                )

                assert response.status_code == 403
                data = response.json()

                # Should have message field for custom error format
                assert "message" in data
                assert "admin permission required" in data["message"].lower()
