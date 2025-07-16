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

    def test_random_sentence_success(self, client: TestClient, read_headers):
        """Test random sentence endpoint successfully retrieves a sentence."""
        response = client.get(f"{SENTENCES_PREFIX}/random", headers=read_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "content" in data and "translation" in data
        assert "id" in data

    def test_random_sentence_not_found(self, client: TestClient, read_headers):
        """Test random sentence endpoint returns 404 if no sentence matches."""
        # Use a verb_id that is highly unlikely to exist
        non_existent_verb_id = uuid4()
        response = client.get(
            f"{SENTENCES_PREFIX}/random?verb_id={non_existent_verb_id}",
            headers=read_headers,
        )
        assert response.status_code == 404
        assert "no sentences found" in response.json()["detail"].lower()

    def test_list_sentences_success(self, client: TestClient, read_headers):
        """Test list sentences endpoint successfully retrieves sentences."""
        response = client.get(f"{SENTENCES_PREFIX}/", headers=read_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)

    def test_get_sentence_by_id_not_found(self, client: TestClient, read_headers):
        """Test retrieving a non-existent sentence by ID returns 404."""
        non_existent_id = uuid4()
        response = client.get(f"{SENTENCES_PREFIX}/{non_existent_id}", headers=read_headers)
        assert response.status_code == 404
        assert "sentence not found" in response.json()["detail"].lower()

    def test_delete_sentence_permission_and_not_found(
        self, client: TestClient, read_headers, write_headers, admin_headers
    ):
        """Test delete sentence permissions and not-found case."""
        non_existent_id = uuid4()

        # 1. Read-only key should be forbidden
        response = client.delete(f"{SENTENCES_PREFIX}/{non_existent_id}", headers=read_headers)
        assert response.status_code == 403
        assert "permission required" in response.json()["detail"].lower()

        # 2. Write key should be allowed, but will return 404 for a non-existent sentence
        response = client.delete(f"{SENTENCES_PREFIX}/{non_existent_id}", headers=write_headers)
        assert response.status_code == 404
        assert "sentence not found" in response.json()["detail"].lower()

        # 3. Admin key should also be allowed and return 404
        response = client.delete(f"{SENTENCES_PREFIX}/{non_existent_id}", headers=admin_headers)
        assert response.status_code == 404
        assert "sentence not found" in response.json()["detail"].lower()

    def test_health_endpoint_bypasses_auth(self, client: TestClient):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

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
