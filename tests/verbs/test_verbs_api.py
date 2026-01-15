"""API contract tests for verb endpoints.

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

from src.main import app

VERBS_PREFIX = "/api/v1/verbs"


# =============================================================================
# Test Client Fixtures with Dependency Overrides
# =============================================================================


@pytest.fixture
def client(monkeypatch):
    """Create a test client with auth disabled and services mocked."""
    from src.core.config import reset_settings
    from src.core.dependencies import get_verb_service
    from src.main import app
    from tests.api.conftest import MockVerbService

    # Disable auth for contract testing
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    reset_settings()

    mock_service = MockVerbService()
    app.dependency_overrides[get_verb_service] = lambda: mock_service

    # Use context manager to run lifespan
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    reset_settings()


@pytest.fixture
def auth_client(test_client_with_lifespan):
    """Provide a test client with real auth enabled for auth tests."""
    return test_client_with_lifespan


# =============================================================================
# Authentication Tests - Use real auth middleware
# =============================================================================


@pytest.mark.security
class TestVerbsAPIAuthentication:
    """Test authentication requirements for verb endpoints."""

    def test_endpoints_require_authentication(self, auth_client: TestClient):
        """Test that all endpoints require authentication."""
        endpoints = [
            f"{VERBS_PREFIX}/random",
            f"{VERBS_PREFIX}/parler",
            f"{VERBS_PREFIX}/parler/conjugations",
        ]

        for endpoint in endpoints:
            response = auth_client.get(endpoint)
            assert response.status_code == 401
            data = response.json()
            assert data["error"] is True
            assert "API key required" in data["message"]

    def test_download_requires_authentication(self, auth_client: TestClient):
        """Test that download endpoint requires authentication."""
        response = auth_client.post(
            f"{VERBS_PREFIX}/download",
            json={"infinitive": "parler", "target_language_code": "eng"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "API key required" in data["message"]

    def test_invalid_api_key_rejected(self, auth_client: TestClient):
        """Test that invalid API keys are rejected."""
        headers = {"Authorization": "Bearer invalid-key-12345"}
        response = auth_client.get(f"{VERBS_PREFIX}/random", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Invalid API key" in data["message"]


# =============================================================================
# Validation Tests - Mock services, test parameter validation
# =============================================================================


@pytest.mark.unit
class TestVerbsAPIValidation:
    """Test request validation with mocked services."""

    def test_method_not_allowed(self, client: TestClient):
        """Test that unsupported HTTP methods are rejected."""
        response = client.post(f"{VERBS_PREFIX}/random")
        assert response.status_code == 405  # Method not allowed

    def test_download_requires_body(self, client: TestClient):
        """Test that download endpoint requires request body."""
        response = client.post(f"{VERBS_PREFIX}/download")
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data


# =============================================================================
# Contract Tests - Mock services, test HTTP behavior
# =============================================================================


@pytest.mark.integration
class TestVerbsAPIContracts:
    """Test API contracts with mocked services."""

    def test_get_verb_by_infinitive_success(self, client: TestClient):
        """Test retrieving an existing verb by its infinitive."""
        response = client.get(f"{VERBS_PREFIX}/parler")
        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert "id" in data

    def test_get_verb_by_infinitive_not_found(self, client: TestClient, monkeypatch):
        """Test retrieving a non-existent verb."""
        from src.core.config import reset_settings
        from src.core.dependencies import get_verb_service
        from tests.api.conftest import MockVerbService

        # Create a mock service that returns None
        mock_service = MockVerbService()
        mock_service.return_none = True
        mock_service.verbs = {}

        monkeypatch.setenv("REQUIRE_AUTH", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        reset_settings()

        app.dependency_overrides[get_verb_service] = lambda: mock_service

        response = client.get(f"{VERBS_PREFIX}/nonexistentverb")
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

        app.dependency_overrides.clear()
        reset_settings()

    def test_get_verb_conjugations_success(self, client: TestClient):
        """Test retrieving conjugations for an existing verb."""
        response = client.get(f"{VERBS_PREFIX}/parler/conjugations")
        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert "conjugations" in data
        assert isinstance(data["conjugations"], list)

    def test_get_verb_conjugations_not_found(self, client: TestClient, monkeypatch):
        """Test retrieving conjugations for a non-existent verb."""
        from src.core.config import reset_settings
        from src.core.dependencies import get_verb_service
        from tests.api.conftest import MockVerbService

        # Create a mock service that returns None
        mock_service = MockVerbService()
        mock_service.return_none = True
        mock_service.verbs = {}

        monkeypatch.setenv("REQUIRE_AUTH", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        reset_settings()

        app.dependency_overrides[get_verb_service] = lambda: mock_service

        response = client.get(f"{VERBS_PREFIX}/nonexistentverb/conjugations")
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

        app.dependency_overrides.clear()
        reset_settings()

    def test_get_random_verb_success(self, client: TestClient):
        """Test retrieving a random verb."""
        response = client.get(f"{VERBS_PREFIX}/random")
        assert response.status_code == 200
        data = response.json()
        assert "infinitive" in data
        assert "id" in data

    def test_download_verb_success(self, client: TestClient):
        """Test downloading conjugations for an existing verb."""
        request_body = {"infinitive": "parler", "target_language_code": "eng"}
        response = client.post(f"{VERBS_PREFIX}/download", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert "infinitive" in data
        assert data["infinitive"] == "parler"
        assert "conjugations" in data

    def test_download_verb_not_found(self, client: TestClient, monkeypatch):
        """Test downloading conjugations for a non-existent verb."""
        from src.core.config import reset_settings
        from src.core.dependencies import get_verb_service
        from tests.api.conftest import MockVerbService

        # Create a mock service that returns None
        mock_service = MockVerbService()
        mock_service.return_none = True
        mock_service.verbs = {}

        monkeypatch.setenv("REQUIRE_AUTH", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        reset_settings()

        app.dependency_overrides[get_verb_service] = lambda: mock_service

        request_body = {"infinitive": "nonexistent", "target_language_code": "eng"}
        response = client.post(f"{VERBS_PREFIX}/download", json=request_body)

        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

        app.dependency_overrides.clear()
        reset_settings()
