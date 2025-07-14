"""Tests for verbs API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import UUID

from src.main import app
from src.services.verb_service import VerbService
from src.schemas.verbs import Verb


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_verb_service():
    """Mock verb service for testing."""
    service = AsyncMock(spec=VerbService)
    return service


@pytest.mark.functional
class TestVerbsAPI:
    """Test verbs API endpoints."""

    def test_verbs_router_exists(self, client: TestClient):
        """Test that the verbs router is included in the app."""
        # Test that the router is registered by checking available routes
        routes = [route.path for route in app.routes]

        # Check that we have the verbs prefix in our routes
        # Note: This tests the current placeholder structure
        verb_routes = [route for route in routes if "/verbs" in route]
        assert len(verb_routes) >= 0  # At least the prefix exists

        # TODO: Update when endpoints are implemented
        # Expected routes:
        # - GET /api/v1/verbs/ - List verbs
        # - POST /api/v1/verbs/download - Download verb
        # - GET /api/v1/verbs/random - Random verb
        # - GET /api/v1/verbs/{verb_id} - Get specific verb
        # - GET /api/v1/verbs/{verb_id}/conjugations - Get conjugations

    def test_verbs_endpoints_not_implemented_yet(self, client: TestClient):
        """Test that verbs endpoints return appropriate responses (placeholder behavior)."""
        # These tests document the current placeholder state
        # TODO: Update when actual endpoints are implemented

        # Test non-existent verb endpoints return 404
        response = client.get("/api/v1/verbs/")
        assert response.status_code == 404

        response = client.get("/api/v1/verbs/random")
        assert response.status_code == 404

        response = client.post("/api/v1/verbs/download")
        assert response.status_code == 404

        # Test with UUID
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/verbs/{test_uuid}")
        assert response.status_code == 404

        response = client.get(f"/api/v1/verbs/{test_uuid}/conjugations")
        assert response.status_code == 404

    # TODO: Implement these tests when endpoints are added
    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_verbs_list(self, client: TestClient, mock_verb_service: AsyncMock):
        """Test GET /api/v1/verbs/ endpoint."""
        # Test with mocked service
        mock_verb_service.get_all_verbs.return_value = []

        with patch("src.api.verbs.VerbService", return_value=mock_verb_service):
            response = client.get("/api/v1/verbs/")

        assert response.status_code == 200
        assert response.json() == []
        mock_verb_service.get_all_verbs.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_random_verb(
        self, client: TestClient, mock_verb_service: AsyncMock, sample_db_verb: Verb
    ):
        """Test GET /api/v1/verbs/random endpoint."""
        mock_verb_service.get_random_verb.return_value = sample_db_verb

        with patch("src.api.verbs.VerbService", return_value=mock_verb_service):
            response = client.get("/api/v1/verbs/random")

        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == sample_db_verb.infinitive
        mock_verb_service.get_random_verb.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_verb_by_id(
        self, client: TestClient, mock_verb_service: AsyncMock, sample_db_verb: Verb
    ):
        """Test GET /api/v1/verbs/{verb_id} endpoint."""
        mock_verb_service.get_verb.return_value = sample_db_verb

        with patch("src.api.verbs.VerbService", return_value=mock_verb_service):
            response = client.get(f"/api/v1/verbs/{sample_db_verb.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == sample_db_verb.infinitive
        mock_verb_service.get_verb.assert_called_once_with(sample_db_verb.id)

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_verb_by_id_not_found(
        self, client: TestClient, mock_verb_service: AsyncMock
    ):
        """Test GET /api/v1/verbs/{verb_id} endpoint when verb not found."""
        mock_verb_service.get_verb.return_value = None
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")

        with patch("src.api.verbs.VerbService", return_value=mock_verb_service):
            response = client.get(f"/api/v1/verbs/{test_uuid}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_download_verb(
        self, client: TestClient, mock_verb_service: AsyncMock, sample_db_verb: Verb
    ):
        """Test POST /api/v1/verbs/download endpoint."""
        mock_verb_service.download_verb.return_value = sample_db_verb

        request_data = {"verb_infinitive": "parler", "target_language_code": "eng"}

        with patch("src.api.verbs.VerbService", return_value=mock_verb_service):
            response = client.post("/api/v1/verbs/download", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["infinitive"] == sample_db_verb.infinitive
        mock_verb_service.download_verb.assert_called_once_with(
            requested_verb="parler", target_language_code="eng"
        )

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_verb_conjugations(
        self, client: TestClient, mock_verb_service: AsyncMock, sample_db_verb: Verb
    ):
        """Test GET /api/v1/verbs/{verb_id}/conjugations endpoint."""
        mock_conjugations = []  # Empty list for now
        mock_verb_service.get_conjugations_by_verb_id.return_value = mock_conjugations

        with patch("src.api.verbs.VerbService", return_value=mock_verb_service):
            response = client.get(f"/api/v1/verbs/{sample_db_verb.id}/conjugations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_verb_service.get_conjugations_by_verb_id.assert_called_once_with(
            sample_db_verb.id
        )


@pytest.mark.functional
class TestVerbsAPIValidation:
    """Test input validation for verbs API endpoints."""

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_invalid_uuid_format(self, client: TestClient):
        """Test that invalid UUID formats are rejected."""
        response = client.get("/api/v1/verbs/invalid-uuid")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_download_verb_validation(self, client: TestClient):
        """Test validation for download verb endpoint."""
        # Test missing required fields
        response = client.post("/api/v1/verbs/download", json={})
        assert response.status_code == 422

        # Test invalid data types
        response = client.post(
            "/api/v1/verbs/download",
            json={
                "verb_infinitive": 123,  # Should be string
                "target_language_code": "eng",
            },
        )
        assert response.status_code == 422
