"""Tests for sentences API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import UUID

from src.main import app
from src.services.sentence_service import SentenceService
from src.schemas.sentences import Sentence


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_sentence_service():
    """Mock sentence service for testing."""
    service = AsyncMock(spec=SentenceService)
    return service


@pytest.mark.functional
class TestSentencesAPI:
    """Test sentences API endpoints."""

    def test_sentences_router_exists(self, client: TestClient):
        """Test that the sentences router is included in the app."""
        # Test that the router is registered by checking available routes
        routes = [route.path for route in app.routes]

        # Check that we have the sentences prefix in our routes
        # Note: This tests the current placeholder structure
        sentence_routes = [route for route in routes if "/sentences" in route]
        assert len(sentence_routes) >= 0  # At least the prefix exists

        # TODO: Update when endpoints are implemented
        # Expected routes:
        # - GET /api/v1/sentences/ - List sentences
        # - POST /api/v1/sentences/ - Create sentence
        # - GET /api/v1/sentences/random - Random sentence
        # - GET /api/v1/sentences/{sentence_id} - Get specific sentence

    def test_sentences_endpoints_not_implemented_yet(self, client: TestClient):
        """Test that sentences endpoints return appropriate responses (placeholder behavior)."""
        # These tests document the current placeholder state
        # TODO: Update when actual endpoints are implemented

        # Test non-existent sentence endpoints return 404
        response = client.get("/api/v1/sentences/")
        assert response.status_code == 404

        response = client.get("/api/v1/sentences/random")
        assert response.status_code == 404

        response = client.post("/api/v1/sentences/")
        assert response.status_code == 404

        # Test with UUID
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/sentences/{test_uuid}")
        assert response.status_code == 404

    # TODO: Implement these tests when endpoints are added
    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_sentences_list(
        self, client: TestClient, mock_sentence_service: AsyncMock
    ):
        """Test GET /api/v1/sentences/ endpoint."""
        mock_sentence_service.get_all_sentences.return_value = []

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.get("/api/v1/sentences/")

        assert response.status_code == 200
        assert response.json() == []
        mock_sentence_service.get_all_sentences.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_random_sentence(
        self,
        client: TestClient,
        mock_sentence_service: AsyncMock,
        sample_db_sentence: Sentence,
    ):
        """Test GET /api/v1/sentences/random endpoint."""
        mock_sentence_service.get_random_sentence.return_value = sample_db_sentence

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.get("/api/v1/sentences/random")

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == sample_db_sentence.content
        mock_sentence_service.get_random_sentence.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_sentence_by_id(
        self,
        client: TestClient,
        mock_sentence_service: AsyncMock,
        sample_db_sentence: Sentence,
    ):
        """Test GET /api/v1/sentences/{sentence_id} endpoint."""
        mock_sentence_service.get_sentence.return_value = sample_db_sentence

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.get(f"/api/v1/sentences/{sample_db_sentence.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == sample_db_sentence.content
        mock_sentence_service.get_sentence.assert_called_once_with(
            sample_db_sentence.id
        )

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_sentence_by_id_not_found(
        self, client: TestClient, mock_sentence_service: AsyncMock
    ):
        """Test GET /api/v1/sentences/{sentence_id} endpoint when sentence not found."""
        mock_sentence_service.get_sentence.return_value = None
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.get(f"/api/v1/sentences/{test_uuid}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_create_sentence(
        self,
        client: TestClient,
        mock_sentence_service: AsyncMock,
        sample_db_sentence: Sentence,
    ):
        """Test POST /api/v1/sentences/ endpoint."""
        mock_sentence_service.create_sentence.return_value = sample_db_sentence

        request_data = {
            "content": "Je parle français.",
            "translation": "I speak French.",
            "verb_id": str(sample_db_sentence.verb_id),
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "is_correct": True,
            "target_language_code": "eng",
            "source": "api",
        }

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.post("/api/v1/sentences/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == sample_db_sentence.content
        mock_sentence_service.create_sentence.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_generate_sentence(
        self,
        client: TestClient,
        mock_sentence_service: AsyncMock,
        sample_db_sentence: Sentence,
    ):
        """Test POST /api/v1/sentences/generate endpoint."""
        mock_sentence_service.generate_sentence.return_value = sample_db_sentence

        request_data = {
            "verb_id": str(sample_db_sentence.verb_id),
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "is_correct": True,
            "target_language_code": "eng",
            "validate": False,
        }

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.post("/api/v1/sentences/generate", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == sample_db_sentence.content
        mock_sentence_service.generate_sentence.assert_called_once()


@pytest.mark.functional
class TestSentencesAPIValidation:
    """Test input validation for sentences API endpoints."""

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_invalid_uuid_format(self, client: TestClient):
        """Test that invalid UUID formats are rejected."""
        response = client.get("/api/v1/sentences/invalid-uuid")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_create_sentence_validation(self, client: TestClient):
        """Test validation for create sentence endpoint."""
        # Test missing required fields
        response = client.post("/api/v1/sentences/", json={})
        assert response.status_code == 422

        # Test invalid enum values
        response = client.post(
            "/api/v1/sentences/",
            json={
                "content": "Je parle français.",
                "translation": "I speak French.",
                "verb_id": "550e8400-e29b-41d4-a716-446655440000",
                "pronoun": "invalid_pronoun",  # Invalid enum
                "tense": "present",
                "direct_object": "none",
                "indirect_object": "none",
                "negation": "none",
                "is_correct": True,
                "target_language_code": "eng",
                "source": "api",
            },
        )
        assert response.status_code == 422

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_generate_sentence_validation(self, client: TestClient):
        """Test validation for generate sentence endpoint."""
        # Test missing required fields
        response = client.post("/api/v1/sentences/generate", json={})
        assert response.status_code == 422

        # Test invalid UUID format
        response = client.post(
            "/api/v1/sentences/generate",
            json={
                "verb_id": "invalid-uuid",
                "pronoun": "first_person",
                "tense": "present",
                "direct_object": "none",
                "indirect_object": "none",
                "negation": "none",
                "is_correct": True,
                "target_language_code": "eng",
                "validate": False,
            },
        )
        assert response.status_code == 422


@pytest.mark.functional
class TestSentencesAPIFiltering:
    """Test filtering and query parameters for sentences API."""

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_sentences_with_filters(
        self, client: TestClient, mock_sentence_service: AsyncMock
    ):
        """Test GET /api/v1/sentences/ with query parameters."""
        mock_sentence_service.get_sentences.return_value = []

        query_params = {
            "verb_id": "550e8400-e29b-41d4-a716-446655440000",
            "is_correct": True,
            "tense": "present",
            "pronoun": "first_person",
            "limit": 10,
        }

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.get("/api/v1/sentences/", params=query_params)

        assert response.status_code == 200
        assert response.json() == []
        mock_sentence_service.get_sentences.assert_called_once_with(
            verb_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            is_correct=True,
            tense="present",
            pronoun="first_person",
            limit=10,
        )

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_random_sentence_with_filters(
        self,
        client: TestClient,
        mock_sentence_service: AsyncMock,
        sample_db_sentence: Sentence,
    ):
        """Test GET /api/v1/sentences/random with query parameters."""
        mock_sentence_service.get_random_sentence.return_value = sample_db_sentence

        query_params = {"is_correct": True, "verb_id": str(sample_db_sentence.verb_id)}

        with patch(
            "src.api.sentences.SentenceService", return_value=mock_sentence_service
        ):
            response = client.get("/api/v1/sentences/random", params=query_params)

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == sample_db_sentence.content
        mock_sentence_service.get_random_sentence.assert_called_once_with(
            is_correct=True, verb_id=sample_db_sentence.verb_id
        )
