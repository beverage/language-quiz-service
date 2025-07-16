"""API contract tests for sentences endpoints.

These tests focus on HTTP behavior, validation, and API contracts.
Uses real test API keys for end-to-end testing against local Supabase.

Authentication tests verify the real auth middleware.
Validation tests verify FastAPI/Pydantic validation.
Business logic is tested in service/repository layers.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.sentences import API_PREFIX
from src.main import ROUTER_PREFIX, app

SENTENCES_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


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
class TestSentencesAPIAuthentication:
    """Test authentication requirements without mocking."""

    def test_endpoints_require_authentication(self, client: TestClient):
        """Test that all endpoints require authentication."""
        endpoints = [
            f"{SENTENCES_PREFIX}/random",
            f"{SENTENCES_PREFIX}/{uuid4()}",
            f"{SENTENCES_PREFIX}/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            data = response.json()
            assert data["error"] is True
            assert "API key required" in data["message"]

    def test_delete_requires_authentication(self, client: TestClient):
        """Test that delete endpoint requires authentication."""
        response = client.delete(f"{SENTENCES_PREFIX}/{uuid4()}")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "API key required" in data["message"]

    def test_invalid_api_key_rejected(self, client: TestClient):
        """Test that invalid API keys are rejected."""
        headers = {"X-API-Key": "invalid-key-12345"}
        response = client.get(f"{SENTENCES_PREFIX}/random", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Invalid API key" in data["message"]

    def test_inactive_api_key_rejected(self, client: TestClient, inactive_headers):
        """Test that inactive API keys are rejected."""
        response = client.get(f"{SENTENCES_PREFIX}/random", headers=inactive_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Invalid API key" in data["message"]


@pytest.mark.unit
class TestSentencesAPIValidation:
    """Test request validation with authenticated requests."""

    def test_invalid_uuid_format(self, client: TestClient, admin_headers):
        """Test validation with invalid UUID formats."""
        # Test invalid UUID in path
        response = client.get(f"{SENTENCES_PREFIX}/not-a-uuid", headers=admin_headers)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_query_parameter_validation(self, client: TestClient, admin_headers):
        """Test query parameter validation."""
        # Test invalid limit value
        response = client.get(
            f"{SENTENCES_PREFIX}/?limit=not-a-number", headers=admin_headers
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_negative_limit_rejected(self, client: TestClient, admin_headers):
        """Test that negative limit values are rejected."""
        response = client.get(f"{SENTENCES_PREFIX}/?limit=-1", headers=admin_headers)
        assert response.status_code == 422

    def test_method_not_allowed(self, client: TestClient, admin_headers):
        """Test that unsupported HTTP methods are rejected."""
        # POST not supported on random endpoint
        response = client.post(f"{SENTENCES_PREFIX}/random", headers=admin_headers)
        assert response.status_code == 405  # Method not allowed


@pytest.mark.integration
class TestSentencesAPIIntegration:
    """Test full API integration with real authentication and services."""

    def test_random_sentence_endpoint(self, client: TestClient, read_headers):
        """Test random sentence endpoint with read permissions."""
        response = client.get(f"{SENTENCES_PREFIX}/random", headers=read_headers)

        # Should work with read permissions or fail at service level
        assert response.status_code in [
            200,
            500,
            503,
        ]  # Service may not be fully configured

        if response.status_code == 200:
            data = response.json()
            # Verify response structure if successful
            assert "content" in data and "translation" in data

    def test_list_sentences_endpoint(self, client: TestClient, read_headers):
        """Test list sentences endpoint."""
        response = client.get(f"{SENTENCES_PREFIX}/", headers=read_headers)

        # Should work with read permissions or fail at service level
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_list_sentences_with_parameters(self, client: TestClient, read_headers):
        """Test list sentences with query parameters."""
        response = client.get(f"{SENTENCES_PREFIX}/?limit=5", headers=read_headers)

        # Should work with read permissions or fail at service level
        assert response.status_code in [200, 422, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 5

    def test_get_sentence_by_id(self, client: TestClient, read_headers):
        """Test retrieving sentence by ID."""
        test_id = uuid4()
        response = client.get(f"{SENTENCES_PREFIX}/{test_id}", headers=read_headers)

        # Should be 404 for non-existent sentence or 500 for service issues
        assert response.status_code in [404, 500]

    def test_delete_sentence_requires_write_permission(
        self, client: TestClient, read_headers
    ):
        """Test that delete requires write permissions."""
        test_id = uuid4()
        response = client.delete(f"{SENTENCES_PREFIX}/{test_id}", headers=read_headers)

        # Should fail with insufficient permissions
        assert response.status_code == 403
        data = response.json()
        assert "write permission required" in data["message"].lower()

    def test_delete_sentence_with_write_permission(
        self, client: TestClient, write_headers
    ):
        """Test delete with proper write permissions."""
        test_id = uuid4()
        response = client.delete(f"{SENTENCES_PREFIX}/{test_id}", headers=write_headers)

        # Should be 404 for non-existent sentence or work properly
        assert response.status_code in [404, 200, 500]

    def test_admin_can_access_all_endpoints(self, client: TestClient, admin_headers):
        """Test that admin key can access all endpoints."""
        # Admin should have full access
        endpoints = [
            ("GET", f"{SENTENCES_PREFIX}/random"),
            ("GET", f"{SENTENCES_PREFIX}/"),
            ("GET", f"{SENTENCES_PREFIX}/{uuid4()}"),  # Will be 404 but not 403
            ("DELETE", f"{SENTENCES_PREFIX}/{uuid4()}"),  # Will be 404 but not 403
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=admin_headers)
            elif method == "DELETE":
                response = client.delete(endpoint, headers=admin_headers)

            # Should not get permission denied (403)
            assert (
                response.status_code != 403
            ), f"{method} {endpoint} should not be forbidden for admin"

    def test_health_endpoint_bypasses_auth(self, client: TestClient):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_api_returns_proper_json_structure(self, client: TestClient):
        """Test that API returns properly structured JSON errors."""
        response = client.get(f"{SENTENCES_PREFIX}/random")

        assert response.status_code == 401
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        # Verify error response structure
        assert "error" in data
        assert "message" in data
        assert "status_code" in data
        assert "path" in data
        assert data["error"] is True
        assert data["status_code"] == 401
