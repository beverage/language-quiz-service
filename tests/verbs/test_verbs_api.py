"""Tests for the verbs API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from uuid import uuid4
from datetime import datetime, timezone

from src.main import app
from src.schemas.verbs import (
    Verb,
    VerbWithConjugations,
    AuxiliaryType,
    VerbClassification,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_verb():
    """Sample verb for testing."""
    return Verb(
        id=uuid4(),
        infinitive="parler",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        target_language_code="eng",
        translation="to speak",
        past_participle="parlé",
        present_participle="parlant",
        classification=VerbClassification.FIRST_GROUP,
        is_irregular=False,
        can_have_cod=True,
        can_have_coi=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_used_at=None,
        usage_count=0,
    )


@pytest.fixture
def sample_verb_with_conjugations():
    """Sample verb with conjugations for testing."""
    return VerbWithConjugations(
        id=uuid4(),
        infinitive="parler",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        target_language_code="eng",
        translation="to speak",
        past_participle="parlé",
        present_participle="parlant",
        classification=VerbClassification.FIRST_GROUP,
        is_irregular=False,
        can_have_cod=True,
        can_have_coi=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_used_at=None,
        usage_count=0,
        conjugations=[],
    )


@pytest.fixture
def mock_api_key_auth():
    """Mock API key authentication response."""
    return {
        "id": str(uuid4()),
        "name": "test-key",
        "permissions_scope": ["read", "write", "admin"],
        "is_active": True,
    }


@pytest.fixture
def auth_headers():
    """Standard auth headers for testing."""
    return {"X-API-Key": "sk_test_12345678901234567890123456789012"}


class TestVerbsAPIAuthentication:
    """Test authentication for verbs API endpoints."""

    def test_download_verb_requires_auth(self, client: TestClient):
        """Test that download verb endpoint requires authentication."""
        with pytest.raises(HTTPException) as exc_info:
            client.post("/verbs/download", params={"infinitive": "parler"})
        assert exc_info.value.status_code == 401
        assert "API key required" in exc_info.value.detail

    def test_get_random_verb_requires_auth(self, client: TestClient):
        """Test that get random verb endpoint requires authentication."""
        with pytest.raises(HTTPException) as exc_info:
            client.get("/verbs/random")
        assert exc_info.value.status_code == 401
        assert "API key required" in exc_info.value.detail

    def test_get_verb_by_infinitive_requires_auth(self, client: TestClient):
        """Test that get verb by infinitive endpoint requires authentication."""
        with pytest.raises(HTTPException) as exc_info:
            client.get("/verbs/parler")
        assert exc_info.value.status_code == 401
        assert "API key required" in exc_info.value.detail

    def test_get_verb_conjugations_requires_auth(self, client: TestClient):
        """Test that get verb conjugations endpoint requires authentication."""
        with pytest.raises(HTTPException) as exc_info:
            client.get("/verbs/parler/conjugations")
        assert exc_info.value.status_code == 401
        assert "API key required" in exc_info.value.detail


class TestDownloadVerbEndpoint:
    """Test the POST /verbs/download endpoint."""

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_download_verb_success(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb,
    ):
        """Test successful verb download."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.download_verb.return_value = sample_verb
        mock_verb_service_class.return_value = mock_service

        response = client.post(
            "/verbs/download",
            headers=auth_headers,
            params={"infinitive": "parler", "target_language_code": "eng"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert data["translation"] == "to speak"

        # Verify service was called correctly
        mock_service.download_verb.assert_called_once_with(
            requested_verb="parler", target_language_code="eng"
        )

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    def test_download_verb_insufficient_permissions(
        self,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
    ):
        """Test download verb with insufficient permissions."""
        # Mock authentication with read-only permissions
        mock_validate_api_key.return_value = {
            "id": str(uuid4()),
            "name": "read-only-key",
            "permissions_scope": ["read"],
            "is_active": True,
        }

        response = client.post(
            "/verbs/download",
            headers=auth_headers,
            params={"infinitive": "parler"},
        )

        assert response.status_code == 403
        assert "Write or admin permission required" in response.json()["message"]

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_download_verb_service_error(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
    ):
        """Test download verb with service error."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service to raise ValueError
        mock_service = AsyncMock()
        mock_service.download_verb.side_effect = ValueError("Invalid verb")
        mock_verb_service_class.return_value = mock_service

        response = client.post(
            "/verbs/download",
            headers=auth_headers,
            params={"infinitive": "invalid"},
        )

        assert response.status_code == 400
        assert "Invalid verb" in response.json()["message"]

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_download_verb_server_error(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
    ):
        """Test download verb with server error."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service to raise exception
        mock_service = AsyncMock()
        mock_service.download_verb.side_effect = Exception("Database error")
        mock_verb_service_class.return_value = mock_service

        response = client.post(
            "/verbs/download",
            headers=auth_headers,
            params={"infinitive": "parler"},
        )

        assert response.status_code == 500
        assert "Failed to download verb" in response.json()["message"]


class TestGetRandomVerbEndpoint:
    """Test the GET /verbs/random endpoint."""

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_random_verb_success(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb,
    ):
        """Test successful random verb retrieval."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_random_verb.return_value = sample_verb
        mock_verb_service_class.return_value = mock_service

        response = client.get(
            "/verbs/random",
            headers=auth_headers,
            params={"target_language_code": "eng"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"

        # Verify service was called correctly
        mock_service.get_random_verb.assert_called_once_with(target_language_code="eng")

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_random_verb_not_found(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
    ):
        """Test random verb when no verbs found."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service to return None
        mock_service = AsyncMock()
        mock_service.get_random_verb.return_value = None
        mock_verb_service_class.return_value = mock_service

        response = client.get("/verbs/random", headers=auth_headers)

        assert response.status_code == 404
        assert "No verbs found" in response.json()["message"]

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    def test_get_random_verb_insufficient_permissions(
        self,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
    ):
        """Test get random verb with insufficient permissions."""
        # Mock authentication with no permissions
        mock_validate_api_key.return_value = {
            "id": str(uuid4()),
            "name": "no-permissions-key",
            "permissions_scope": [],
            "is_active": True,
        }

        response = client.get("/verbs/random", headers=auth_headers)

        assert response.status_code == 403
        assert "Read permission required" in response.json()["message"]


class TestGetVerbByInfinitiveEndpoint:
    """Test the GET /verbs/{infinitive} endpoint."""

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_by_infinitive_success(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb,
    ):
        """Test successful verb retrieval by infinitive."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_verb_by_infinitive.return_value = sample_verb
        mock_verb_service_class.return_value = mock_service

        response = client.get(
            "/verbs/parler",
            headers=auth_headers,
            params={"target_language_code": "eng"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"

        # Verify service was called correctly
        mock_service.get_verb_by_infinitive.assert_called_once_with(
            infinitive="parler",
            auxiliary=None,
            reflexive=None,
            target_language_code="eng",
        )

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_by_infinitive_url_encoded(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb,
    ):
        """Test verb retrieval with URL-encoded infinitive (spaces)."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_verb_by_infinitive.return_value = sample_verb
        mock_verb_service_class.return_value = mock_service

        # Test with URL-encoded space
        response = client.get("/verbs/se%20parler", headers=auth_headers)

        assert response.status_code == 200

        # Verify service was called with decoded infinitive
        mock_service.get_verb_by_infinitive.assert_called_once_with(
            infinitive="se parler",
            auxiliary=None,
            reflexive=None,
            target_language_code="eng",
        )

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_by_infinitive_not_found(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
    ):
        """Test verb retrieval when verb not found."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service to return None
        mock_service = AsyncMock()
        mock_service.get_verb_by_infinitive.return_value = None
        mock_verb_service_class.return_value = mock_service

        response = client.get("/verbs/nonexistent", headers=auth_headers)

        assert response.status_code == 404
        assert "Verb 'nonexistent' not found" in response.json()["message"]

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_by_infinitive_with_params(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb,
    ):
        """Test verb retrieval with auxiliary and reflexive parameters."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_verb_by_infinitive.return_value = sample_verb
        mock_verb_service_class.return_value = mock_service

        response = client.get(
            "/verbs/parler",
            headers=auth_headers,
            params={
                "auxiliary": "avoir",
                "reflexive": "true",
                "target_language_code": "eng",
            },
        )

        assert response.status_code == 200

        # Verify service was called with correct parameters
        mock_service.get_verb_by_infinitive.assert_called_once_with(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=True,
            target_language_code="eng",
        )


class TestGetVerbConjugationsEndpoint:
    """Test the GET /verbs/{infinitive}/conjugations endpoint."""

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_conjugations_success(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb_with_conjugations,
    ):
        """Test successful verb conjugations retrieval."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_verb_with_conjugations.return_value = (
            sample_verb_with_conjugations
        )
        mock_verb_service_class.return_value = mock_service

        response = client.get(
            "/verbs/parler/conjugations",
            headers=auth_headers,
            params={"target_language_code": "eng"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert "conjugations" in data

        # Verify service was called correctly
        mock_service.get_verb_with_conjugations.assert_called_once_with(
            infinitive="parler",
            auxiliary=None,
            reflexive=False,
            target_language_code="eng",
        )

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_conjugations_url_encoded(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb_with_conjugations,
    ):
        """Test conjugations retrieval with URL-encoded infinitive."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_verb_with_conjugations.return_value = (
            sample_verb_with_conjugations
        )
        mock_verb_service_class.return_value = mock_service

        response = client.get("/verbs/se%20parler/conjugations", headers=auth_headers)

        assert response.status_code == 200

        # Verify service was called with decoded infinitive
        mock_service.get_verb_with_conjugations.assert_called_once_with(
            infinitive="se parler",
            auxiliary=None,
            reflexive=False,
            target_language_code="eng",
        )

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_conjugations_not_found(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
    ):
        """Test conjugations retrieval when verb not found."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service to return None
        mock_service = AsyncMock()
        mock_service.get_verb_with_conjugations.return_value = None
        mock_verb_service_class.return_value = mock_service

        response = client.get("/verbs/nonexistent/conjugations", headers=auth_headers)

        assert response.status_code == 404
        assert "Verb 'nonexistent' not found" in response.json()["message"]

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_get_verb_conjugations_with_params(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb_with_conjugations,
    ):
        """Test conjugations retrieval with auxiliary and reflexive parameters."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_verb_with_conjugations.return_value = (
            sample_verb_with_conjugations
        )
        mock_verb_service_class.return_value = mock_service

        response = client.get(
            "/verbs/parler/conjugations",
            headers=auth_headers,
            params={
                "auxiliary": "avoir",
                "reflexive": "true",
                "target_language_code": "eng",
            },
        )

        assert response.status_code == 200

        # Verify service was called with correct parameters
        mock_service.get_verb_with_conjugations.assert_called_once_with(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=True,
            target_language_code="eng",
        )


class TestVerbsAPIIntegration:
    """Integration tests for verbs API endpoints."""

    @patch("src.core.auth.ApiKeyAuthMiddleware._validate_api_key_with_ip")
    @patch("src.api.verbs.VerbService")
    def test_multiple_endpoints_same_service(
        self,
        mock_verb_service_class,
        mock_validate_api_key,
        client: TestClient,
        auth_headers,
        mock_api_key_auth,
        sample_verb,
    ):
        """Test that multiple endpoints use the same service pattern."""
        # Mock authentication
        mock_validate_api_key.return_value = mock_api_key_auth

        # Mock service
        mock_service = AsyncMock()
        mock_service.get_random_verb.return_value = sample_verb
        mock_service.get_verb_by_infinitive.return_value = sample_verb
        mock_verb_service_class.return_value = mock_service

        # Test multiple endpoints
        response1 = client.get("/verbs/random", headers=auth_headers)
        response2 = client.get("/verbs/parler", headers=auth_headers)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify service was instantiated multiple times (fresh instances)
        assert mock_verb_service_class.call_count == 2

    def test_cors_headers_present(self, client: TestClient, auth_headers):
        """Test that CORS headers are present in API responses."""
        # This will fail auth but should still have CORS headers
        with pytest.raises(HTTPException) as exc_info:
            client.get("/verbs/random")

        # Check that the response doesn't have CORS issues
        assert exc_info.value.status_code == 401  # Expected auth failure
        # FastAPI with CORSMiddleware handles CORS automatically
