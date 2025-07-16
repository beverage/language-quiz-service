"""Clean API contract tests for verbs endpoints.

These tests focus on HTTP request/response behavior, parameter handling,
and API contract validation without complex dependency injection.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.schemas.verbs import (
    AuxiliaryType,
    Verb,
    VerbClassification,
    VerbCreate,
    VerbWithConjugations,
)

# Import fixtures from verbs domain
from tests.verbs.fixtures import generate_random_verb_data, sample_verb


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_verb_data():
    """Generate sample verb data for testing."""
    data = generate_random_verb_data()
    return VerbCreate(**data)


@pytest.fixture
def sample_verb_with_conjugations(sample_verb):
    """Create a sample VerbWithConjugations instance."""
    return VerbWithConjugations(**sample_verb.model_dump(), conjugations=[])


@pytest.fixture
def mock_api_key_info():
    """Mock API key info for authorization."""
    return {
        "id": str(uuid4()),
        "key_prefix": "sk_test_verb",
        "name": "Verb Test Key",
        "description": "Test API key for verbs",
        "client_name": "test-client",
        "is_active": True,
        "permissions_scope": ["read", "write", "admin"],
        "created_at": datetime.now().isoformat(),
        "last_used_at": None,
        "usage_count": 0,
        "rate_limit_rpm": 1000,
        "allowed_ips": ["127.0.0.1"],
    }


@pytest.fixture
def auth_headers():
    """Standard auth headers for testing."""
    return {"X-API-Key": "sk_test_12345678901234567890123456789012"}


def _mock_auth_middleware(mock_key_info):
    """Helper to mock the authentication middleware for isolated testing."""

    async def mock_dispatch(request, call_next):
        # Mock the request state with API key info
        request.state.api_key_info = mock_key_info
        request.state.client_ip = "127.0.0.1"
        return await call_next(request)

    return patch(
        "src.core.auth.ApiKeyAuthMiddleware.dispatch", side_effect=mock_dispatch
    )


class TestVerbsAPIContract:
    """Test HTTP contract and API behavior for verbs endpoints."""

    def test_get_random_verb_success(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test successful random verb retrieval."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                # Mock service instance and method
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_random_verb.return_value = sample_verb

                response = client.get(
                    "/verbs/random",
                    headers=auth_headers,
                    params={"target_language_code": "eng"},
                )

                # Verify HTTP contract
                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "id" in data
                assert "infinitive" in data
                assert "translation" in data
                assert "auxiliary" in data
                assert "target_language_code" in data
                assert data["infinitive"] == "parler"
                assert data["translation"] == "to speak"

                # Verify service was called correctly
                mock_service.get_random_verb.assert_called_once_with(
                    target_language_code="eng"
                )

    def test_get_random_verb_not_found(
        self, client: TestClient, auth_headers, mock_api_key_info
    ):
        """Test random verb when no verbs found."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_random_verb.return_value = None

                response = client.get("/verbs/random", headers=auth_headers)

                assert response.status_code == 404
                data = response.json()
                assert (
                    "not found" in data["message"].lower()
                    or "no verbs found" in data["message"].lower()
                )

    def test_get_verb_by_infinitive_success(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test successful verb retrieval by infinitive."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb

                response = client.get(
                    "/verbs/parler",
                    headers=auth_headers,
                    params={"target_language_code": "eng"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["infinitive"] == "parler"
                assert data["id"] == str(sample_verb.id)

                # Verify service was called correctly
                mock_service.get_verb_by_infinitive.assert_called_once_with(
                    infinitive="parler",
                    auxiliary=None,
                    reflexive=None,
                    target_language_code="eng",
                )

    def test_get_verb_by_infinitive_not_found(
        self, client: TestClient, auth_headers, mock_api_key_info
    ):
        """Test verb retrieval when verb doesn't exist."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = None

                response = client.get("/verbs/nonexistent", headers=auth_headers)

                assert response.status_code == 404
                data = response.json()
                assert "not found" in data["message"].lower()
                assert "nonexistent" in data["message"]

    def test_get_verb_by_infinitive_with_url_encoding(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test verb retrieval with URL-encoded infinitive (spaces)."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                # Update sample verb to have space in infinitive
                sample_verb.infinitive = "se parler"
                mock_service.get_verb_by_infinitive.return_value = sample_verb

                # Test with URL-encoded space
                response = client.get("/verbs/se%20parler", headers=auth_headers)

                assert response.status_code == 200
                data = response.json()
                assert data["infinitive"] == "se parler"

                # Verify service was called with decoded infinitive
                mock_service.get_verb_by_infinitive.assert_called_once_with(
                    infinitive="se parler",
                    auxiliary=None,
                    reflexive=None,
                    target_language_code="eng",
                )

    def test_get_verb_by_infinitive_with_parameters(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test verb retrieval with auxiliary and reflexive parameters."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb

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
                data = response.json()
                assert data["auxiliary"] == "avoir"

                # Verify service was called with correct parameters
                mock_service.get_verb_by_infinitive.assert_called_once_with(
                    infinitive="parler",
                    auxiliary="avoir",
                    reflexive=True,
                    target_language_code="eng",
                )

    def test_get_verb_conjugations_success(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        sample_verb_with_conjugations,
    ):
        """Test successful verb conjugations retrieval."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_with_conjugations.return_value = (
                    sample_verb_with_conjugations
                )

                response = client.get(
                    "/verbs/parler/conjugations",
                    headers=auth_headers,
                    params={"target_language_code": "eng"},
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure includes conjugations
                assert "id" in data
                assert "infinitive" in data
                assert "conjugations" in data
                assert data["infinitive"] == "parler"
                assert isinstance(data["conjugations"], list)

                # Verify service was called correctly
                mock_service.get_verb_with_conjugations.assert_called_once_with(
                    infinitive="parler",
                    auxiliary=None,
                    reflexive=False,
                    target_language_code="eng",
                )

    def test_get_verb_conjugations_not_found(
        self, client: TestClient, auth_headers, mock_api_key_info
    ):
        """Test conjugations retrieval when verb doesn't exist."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_with_conjugations.return_value = None

                response = client.get(
                    "/verbs/nonexistent/conjugations", headers=auth_headers
                )

                assert response.status_code == 404
                data = response.json()
                assert "not found" in data["message"].lower()

    def test_download_verb_success(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test successful verb download (creation via external API)."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.download_verb.return_value = sample_verb

                response = client.post(
                    "/verbs/download",
                    headers=auth_headers,
                    params={"infinitive": "parler", "target_language_code": "eng"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["infinitive"] == "parler"
                assert "translation" in data

                # Verify service was called correctly
                mock_service.download_verb.assert_called_once_with(
                    requested_verb="parler", target_language_code="eng"
                )

    def test_download_verb_already_exists(
        self, client: TestClient, auth_headers, mock_api_key_info
    ):
        """Test download verb when verb already exists."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                # Simulate verb already exists error
                mock_service.download_verb.side_effect = ValueError(
                    "Verb already exists"
                )

                response = client.post(
                    "/verbs/download",
                    headers=auth_headers,
                    params={"infinitive": "parler", "target_language_code": "eng"},
                )

                assert response.status_code == 400  # ValueError returns 400, not 409
                data = response.json()
                # Response format: {'error': True, 'message': '...', 'status_code': 400, 'path': '/verbs/download'}
                assert "already exists" in data["message"].lower()

    def test_download_verb_invalid_request(
        self, client: TestClient, auth_headers, mock_api_key_info
    ):
        """Test download verb with invalid parameters."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                # Mock to prevent hitting real OpenAI API - use validation error
                mock_service.download_verb.side_effect = ValueError(
                    "Invalid infinitive: cannot be empty"
                )

                response = client.post(
                    "/verbs/download",
                    headers=auth_headers,
                    params={
                        "infinitive": "",  # Empty infinitive
                        "target_language_code": "eng",
                    },
                )

                # Should return 400 for ValueError from service
                assert response.status_code == 400
                data = response.json()
                assert "invalid" in data["message"].lower()


class TestVerbsAPIParameterHandling:
    """Test parameter validation and handling in verbs API."""

    def test_default_target_language(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test that default target language code is applied."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_random_verb.return_value = sample_verb

                response = client.get(
                    "/verbs/random",
                    headers=auth_headers,
                    # No target_language_code parameter
                )

                # Should use default language (eng)
                assert response.status_code == 200
                # Verify service was called with default language
                mock_service.get_random_verb.assert_called_once_with(
                    target_language_code="eng"
                )

    def test_boolean_parameter_parsing(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test that boolean parameters are correctly parsed."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb

                # Test various boolean representations
                for bool_value in ["true", "True", "1"]:
                    response = client.get(
                        "/verbs/parler",
                        headers=auth_headers,
                        params={"reflexive": bool_value},
                    )

                    assert response.status_code == 200
                    # Verify service was called with boolean True
                    mock_service.get_verb_by_infinitive.assert_called_with(
                        infinitive="parler",
                        auxiliary=None,
                        reflexive=True,
                        target_language_code="eng",
                    )

    def test_enum_parameter_validation(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test that enum parameters are validated."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb

                # Test valid auxiliary values
                for aux in ["avoir", "etre"]:
                    response = client.get(
                        "/verbs/parler", headers=auth_headers, params={"auxiliary": aux}
                    )
                    # Should not return 422 (validation error)
                    assert response.status_code == 200


class TestVerbsAPIResponseFormats:
    """Test response format and serialization."""

    def test_verb_response_schema(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test that verb responses match expected schema."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb

                response = client.get("/verbs/parler", headers=auth_headers)

                assert response.status_code == 200
                data = response.json()

                # Required fields
                required_fields = [
                    "id",
                    "infinitive",
                    "auxiliary",
                    "reflexive",
                    "target_language_code",
                    "translation",
                    "past_participle",
                    "present_participle",
                    "classification",
                    "is_irregular",
                    "can_have_cod",
                    "can_have_coi",
                    "created_at",
                    "updated_at",
                ]

                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"

    def test_verb_with_conjugations_response_schema(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        sample_verb_with_conjugations,
    ):
        """Test that verb with conjugations responses include conjugations array."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_with_conjugations.return_value = (
                    sample_verb_with_conjugations
                )

                response = client.get(
                    "/verbs/parler/conjugations", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()

                # Should have all verb fields plus conjugations
                assert "conjugations" in data
                assert isinstance(data["conjugations"], list)

    def test_error_response_format(
        self, client: TestClient, auth_headers, mock_api_key_info
    ):
        """Test that error responses have consistent format."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = None

                response = client.get(
                    "/verbs/definitely_nonexistent_verb", headers=auth_headers
                )

                assert response.status_code == 404
                data = response.json()

                # Error responses should have message field
                assert "message" in data
                assert isinstance(data["message"], str)
                assert len(data["message"]) > 0
