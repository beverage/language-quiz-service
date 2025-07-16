"""API contract tests for API keys endpoints.

These tests focus on HTTP behavior, validation, and API contracts.
Uses real test API keys for end-to-end testing against local Supabase.

Authentication tests verify the real auth middleware.
Validation tests verify FastAPI/Pydantic validation.
Business logic is tested in service/repository layers.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.api_keys import API_PREFIX
from src.main import ROUTER_PREFIX, app

API_KEY_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Headers with admin test API key."""
    return {
        "X-API-Key": "sk_live_adm1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.fixture
def write_headers():
    """Headers with read/write test API key."""
    return {
        "X-API-Key": "sk_live_wrt1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.fixture
def read_headers():
    """Headers with read-only test API key."""
    return {
        "X-API-Key": "sk_live_red1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.fixture
def inactive_headers():
    """Headers with inactive test API key."""
    return {
        "X-API-Key": "sk_live_ina1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.mark.security
class TestApiKeysAPIAuthentication:
    """Test authentication requirements without mocking."""

    def test_endpoints_require_authentication(self, client: TestClient):
        """Test that all endpoints require valid authentication."""
        endpoints = [
            ("GET", f"{API_KEY_PREFIX}/"),
            ("POST", f"{API_KEY_PREFIX}/"),
            ("GET", f"{API_KEY_PREFIX}/stats"),
            ("GET", f"{API_KEY_PREFIX}/current"),
            ("GET", f"{API_KEY_PREFIX}/{uuid4()}"),
            ("PUT", f"{API_KEY_PREFIX}/{uuid4()}"),
            ("DELETE", f"{API_KEY_PREFIX}/{uuid4()}"),
            ("GET", f"{API_KEY_PREFIX}/search?name=test"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert (
                response.status_code == 401
            ), f"{method} {endpoint} should require auth"
            data = response.json()
            assert data["error"] is True
            assert "API key required" in data["message"]

    def test_invalid_api_key_rejected(self, client: TestClient):
        """Test that invalid API keys are rejected."""
        invalid_headers = {"X-API-Key": "invalid_key"}

        response = client.get(f"{API_KEY_PREFIX}/", headers=invalid_headers)
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True

    def test_inactive_api_key_rejected(self, client: TestClient, inactive_headers):
        """Test that inactive API keys are rejected."""
        response = client.get(f"{API_KEY_PREFIX}/", headers=inactive_headers)
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Invalid API key" in data["message"]


@pytest.mark.unit
class TestApiKeysAPIValidation:
    """Test FastAPI/Pydantic validation with authenticated requests."""

    def test_create_api_key_validation_errors(self, client: TestClient, admin_headers):
        """Test validation errors for API key creation."""
        # Missing required fields
        response = client.post(f"{API_KEY_PREFIX}/", json={}, headers=admin_headers)
        assert response.status_code == 422

        # Invalid permissions scope
        from uuid import uuid4

        invalid_data = {
            "name": f"Test Key {uuid4()}",
            "permissions_scope": ["invalid_permission"],
        }
        response = client.post(
            f"{API_KEY_PREFIX}/", json=invalid_data, headers=admin_headers
        )
        assert response.status_code == 422

    def test_list_api_keys_parameter_validation(
        self, client: TestClient, admin_headers
    ):
        """Test parameter validation for listing API keys."""
        # Invalid limit (too high)
        response = client.get(f"{API_KEY_PREFIX}/?limit=1500", headers=admin_headers)
        assert response.status_code == 422

        # Invalid limit (negative)
        response = client.get(f"{API_KEY_PREFIX}/?limit=-1", headers=admin_headers)
        assert response.status_code == 422

    def test_search_missing_required_parameter(self, client: TestClient, admin_headers):
        """Test search endpoint with missing required parameter."""
        response = client.get(f"{API_KEY_PREFIX}/search", headers=admin_headers)
        assert response.status_code == 422

    def test_invalid_uuid_parameters(self, client: TestClient, admin_headers):
        """Test endpoints with invalid UUID parameters."""
        invalid_id = "not-a-uuid"

        # Test get by ID
        response = client.get(f"{API_KEY_PREFIX}/{invalid_id}", headers=admin_headers)
        assert response.status_code == 422

        # Test update by ID
        response = client.put(
            f"{API_KEY_PREFIX}/{invalid_id}",
            json={"name": "Updated"},
            headers=admin_headers,
        )
        assert response.status_code == 422

        # Test delete by ID
        response = client.delete(
            f"{API_KEY_PREFIX}/{invalid_id}", headers=admin_headers
        )
        assert response.status_code == 422


@pytest.mark.security
class TestApiKeysAPIPermissions:
    """Test permission-based access control."""

    def test_create_requires_admin_permission(self, client: TestClient, read_headers):
        """Test that creating API keys requires admin permission."""
        from uuid import uuid4

        create_data = {
            "name": f"Test API Key {uuid4()}",
            "permissions_scope": ["read"],
        }
        response = client.post(
            f"{API_KEY_PREFIX}/", json=create_data, headers=read_headers
        )
        assert response.status_code == 403

        data = response.json()
        assert "admin permission required" in data["message"].lower()

    def test_admin_operations_require_admin_permission(
        self, client: TestClient, read_headers
    ):
        """Test that admin operations require admin permission."""
        key_id = uuid4()

        # Test update
        response = client.put(
            f"{API_KEY_PREFIX}/{key_id}", json={"name": "Updated"}, headers=read_headers
        )
        assert response.status_code == 403

        # Test delete
        response = client.delete(f"{API_KEY_PREFIX}/{key_id}", headers=read_headers)
        assert response.status_code == 403

    def test_stats_require_admin_permission(self, client: TestClient, read_headers):
        """Test that stats endpoint requires admin permission."""
        response = client.get(f"{API_KEY_PREFIX}/stats", headers=read_headers)
        assert response.status_code == 403


@pytest.mark.integration
class TestApiKeysAPIIntegration:
    """Test full API integration with real authentication and services."""

    def test_list_api_keys_success(self, client: TestClient, admin_headers):
        """Test successful API keys listing."""
        response = client.get(f"{API_KEY_PREFIX}/", headers=admin_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list)
        # Should include our active test keys
        assert len(data) >= 3, "Expected at least 3 active test keys"

    def test_list_api_keys_with_parameters(self, client: TestClient, admin_headers):
        """Test API keys listing with query parameters."""
        response = client.get(f"{API_KEY_PREFIX}/?limit=2", headers=admin_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    def test_get_api_key_stats_success(self, client: TestClient, admin_headers):
        """Test successful API key statistics retrieval."""
        response = client.get(f"{API_KEY_PREFIX}/stats", headers=admin_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "total_keys" in data
        assert "active_keys" in data
        assert data["total_keys"] >= 3

    def test_get_current_key_info_success(self, client: TestClient, admin_headers):
        """Test retrieving information about the current key."""
        response = client.get(f"{API_KEY_PREFIX}/current", headers=admin_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["key_prefix"] == "sk_live_adm1"
        assert "admin" in data["permissions_scope"]

    def test_get_api_key_by_id_not_found(self, client: TestClient, admin_headers):
        """Test getting a non-existent API key by ID."""
        non_existent_id = uuid4()
        response = client.get(f"{API_KEY_PREFIX}/{non_existent_id}", headers=admin_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_search_api_keys_not_found(self, client: TestClient, admin_headers):
        """Test searching for API keys with a term that yields no results."""
        search_term = "nonexistentkeysearchterm"
        response = client.get(
            f"{API_KEY_PREFIX}/search?name={search_term}", headers=admin_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_and_revoke_api_key_flow(self, client: TestClient, admin_headers):
        """Test creating, verifying, and then revoking a new API key."""
        # 1. Create a new API key
        key_name = f"Test-Key-{uuid4()}"
        create_data = {"name": key_name, "permissions_scope": ["read"]}
        response = client.post(
            f"{API_KEY_PREFIX}/", json=create_data, headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to create key: {response.text}"
        create_data = response.json()
        new_key_id = create_data["key_info"]["id"]
        assert new_key_id is not None

        # 2. Verify the key can be retrieved
        response = client.get(f"{API_KEY_PREFIX}/{new_key_id}", headers=admin_headers)
        assert response.status_code == 200
        retrieved_data = response.json()
        assert retrieved_data["name"] == key_name
        assert retrieved_data["is_active"] is True

        # 3. Revoke the key
        response = client.delete(f"{API_KEY_PREFIX}/{new_key_id}", headers=admin_headers)
        assert response.status_code == 200
        assert "revoked" in response.json()["message"]

        # 4. Verify the key is now inactive
        response = client.get(f"{API_KEY_PREFIX}/{new_key_id}", headers=admin_headers)
        assert response.status_code == 200
        retrieved_data = response.json()
        assert retrieved_data["is_active"] is False

    def test_update_api_key_not_found(self, client: TestClient, admin_headers):
        """Test updating a non-existent API key."""
        non_existent_id = uuid4()
        update_data = {"name": "This Should Fail"}
        response = client.put(
            f"{API_KEY_PREFIX}/{non_existent_id}",
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_revoke_api_key_not_found(self, client: TestClient, admin_headers):
        """Test revoking a non-existent API key."""
        non_existent_id = uuid4()
        response = client.delete(f"{API_KEY_PREFIX}/{non_existent_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_update_api_key_no_data_provided(
        self, client: TestClient, admin_headers
    ):
        """Test updating an API key with no data should result in a 400."""
        # Find a valid key to update
        response = client.get(f"{API_KEY_PREFIX}/", headers=admin_headers)
        key_id = response.json()[0]["id"]

        response = client.put(
            f"{API_KEY_PREFIX}/{key_id}", json={}, headers=admin_headers
        )
        assert response.status_code == 400
        assert "no update data provided" in response.json()["detail"].lower()
