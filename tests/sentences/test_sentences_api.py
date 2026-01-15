"""API contract tests for sentences endpoints.

These tests focus on HTTP behavior, validation, and API contracts.
Service dependencies are mocked to avoid database/event loop issues.

Test Categories:
- Authentication tests (@pytest.mark.security): Test real auth middleware
- Contract tests (@pytest.mark.integration): Mock services, test HTTP contracts
- Validation tests (@pytest.mark.unit): Mock services, test parameter validation
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.sentences import API_PREFIX
from src.main import ROUTER_PREFIX, app

SENTENCES_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


# =============================================================================
# Test Client Fixtures with Dependency Overrides
# =============================================================================


@pytest.fixture
def client(monkeypatch):
    """Create a test client with auth disabled and services mocked."""
    from src.core.config import reset_settings
    from src.core.dependencies import get_sentence_service
    from src.main import app
    from tests.api.conftest import MockSentenceService

    # Disable auth for contract testing
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    reset_settings()

    mock_service = MockSentenceService()
    app.dependency_overrides[get_sentence_service] = lambda: mock_service

    # Use context manager to run lifespan
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    reset_settings()


@pytest.fixture
def auth_client(test_client_with_lifespan):
    """Provide a test client with real auth enabled for auth tests.

    Uses real API key validation but mocked services.
    """
    return test_client_with_lifespan


# =============================================================================
# Authentication Tests - Use real auth middleware
# =============================================================================


@pytest.mark.security
class TestSentencesAPIAuthentication:
    """Test authentication requirements without mocking."""

    def test_endpoints_require_authentication(self, auth_client: TestClient):
        """Test that all endpoints require authentication."""
        endpoints = [
            f"{SENTENCES_PREFIX}/random",
            f"{SENTENCES_PREFIX}/{uuid4()}",
            f"{SENTENCES_PREFIX}/",
        ]

        for endpoint in endpoints:
            response = auth_client.get(endpoint)
            assert response.status_code == 401
            data = response.json()
            assert data["error"] is True
            assert "API key required" in data["message"]

    def test_delete_requires_authentication(self, auth_client: TestClient):
        """Test that delete endpoint requires authentication."""
        response = auth_client.delete(f"{SENTENCES_PREFIX}/{uuid4()}")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "API key required" in data["message"]

    def test_invalid_api_key_rejected(self, auth_client: TestClient):
        """Test that invalid API keys are rejected."""
        headers = {"Authorization": "Bearer invalid-key-12345"}
        response = auth_client.get(f"{SENTENCES_PREFIX}/random", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Invalid API key" in data["message"]


# =============================================================================
# Validation Tests - Mock services, test parameter validation
# =============================================================================


@pytest.mark.unit
class TestSentencesAPIValidation:
    """Test request validation with mocked services."""

    def test_invalid_uuid_format(self, client: TestClient):
        """Test validation with invalid UUID formats."""
        response = client.get(f"{SENTENCES_PREFIX}/not-a-uuid")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_query_parameter_validation(self, client: TestClient):
        """Test query parameter validation."""
        response = client.get(f"{SENTENCES_PREFIX}/?limit=not-a-number")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_negative_limit_rejected(self, client: TestClient):
        """Test that negative limit values are rejected."""
        response = client.get(f"{SENTENCES_PREFIX}/?limit=-1")
        assert response.status_code == 422

    def test_method_not_allowed(self, client: TestClient):
        """Test that unsupported HTTP methods are rejected."""
        response = client.post(f"{SENTENCES_PREFIX}/random")
        assert response.status_code == 405  # Method not allowed


# =============================================================================
# Contract Tests - Mock services, test HTTP behavior
# =============================================================================


@pytest.mark.integration
class TestSentencesAPIContracts:
    """Test API contracts with mocked services."""

    def test_random_sentence_success(self, client: TestClient):
        """Test random sentence endpoint successfully retrieves a sentence."""
        response = client.get(f"{SENTENCES_PREFIX}/random")
        assert response.status_code == 200

        data = response.json()
        assert "content" in data
        assert "translation" in data
        assert "id" in data

    def test_random_sentence_not_found(self, client: TestClient, monkeypatch):
        """Test random sentence endpoint returns 404 if no sentence matches."""
        from src.core.config import reset_settings
        from src.core.dependencies import get_sentence_service
        from tests.api.conftest import MockSentenceService

        # Create a mock service that returns None
        mock_service = MockSentenceService()
        mock_service.return_none = True
        mock_service.sentences = {}

        monkeypatch.setenv("REQUIRE_AUTH", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        reset_settings()

        app.dependency_overrides[get_sentence_service] = lambda: mock_service

        response = client.get(f"{SENTENCES_PREFIX}/random")
        assert response.status_code == 404
        assert "no sentences found" in response.json()["message"].lower()

        app.dependency_overrides.clear()
        reset_settings()

    def test_list_sentences_success(self, client: TestClient):
        """Test list sentences endpoint successfully retrieves sentences."""
        response = client.get(f"{SENTENCES_PREFIX}/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sentence_by_id_not_found(self, client: TestClient):
        """Test retrieving a non-existent sentence by ID returns 404."""
        non_existent_id = uuid4()
        response = client.get(f"{SENTENCES_PREFIX}/{non_existent_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    def test_delete_sentence_not_found(self, client: TestClient):
        """Test deleting a non-existent sentence returns 404."""
        non_existent_id = uuid4()
        response = client.delete(f"{SENTENCES_PREFIX}/{non_existent_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    def test_health_endpoint_bypasses_auth(self, auth_client: TestClient):
        """Test that health endpoint doesn't require authentication."""
        response = auth_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_returns_proper_json_structure(self, auth_client: TestClient):
        """Test that API returns properly structured JSON errors."""
        response = auth_client.get(f"{SENTENCES_PREFIX}/random")

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
