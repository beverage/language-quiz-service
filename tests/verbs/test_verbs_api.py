"""Clean API contract tests for verbs endpoints.

These tests focus on HTTP request/response behavior, parameter handling,
and API contract validation without complex dependency injection.
"""

from contextlib import contextmanager
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.schemas.verbs import (
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
        "is_active": True,
        "rate_limit": 1000,
        "rate_limit_remaining": 1000,
        "rate_limit_reset": datetime.now().timestamp() + 3600,
        "last_used_at": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "permissions_scope": [
            "read",
            "write",
        ],  # Include write permission for download tests
    }


@pytest.fixture
def auth_headers():
    """Basic auth headers for API testing."""
    return {"X-API-Key": "sk_test_valid_key"}


@contextmanager
def _mock_auth_middleware(api_key_info):
    """Context manager to mock auth middleware."""

    async def mock_dispatch(request, call_next):
        request.state.api_key_info = api_key_info
        request.state.client_ip = "127.0.0.1"
        return await call_next(request)

    with patch(
        "src.core.auth.ApiKeyAuthMiddleware.dispatch", side_effect=mock_dispatch
    ):
        yield


class TestVerbsAPIEndpoints:
    """Test verbs API endpoints with success and error cases."""

    @pytest.mark.parametrize(
        "endpoint,method_name,expected_status,return_value,expected_response_keys",
        [
            # Success cases
            (
                "/api/v1/verbs/random?target_language_code=eng",
                "get_random_verb",
                200,
                "sample_verb",
                [
                    "id",
                    "infinitive",
                    "translation",
                    "auxiliary",
                    "target_language_code",
                ],
            ),
            (
                "/api/v1/verbs/parler",
                "get_verb_by_infinitive",
                200,
                "sample_verb",
                ["id", "infinitive", "translation", "auxiliary"],
            ),
            (
                "/api/v1/verbs/parler/conjugations",
                "get_verb_with_conjugations",
                200,
                "sample_verb_with_conjugations",
                ["id", "infinitive", "conjugations"],
            ),
            # Not found cases
            (
                "/api/v1/verbs/random",
                "get_random_verb",
                404,
                None,
                ["message"],
            ),
            (
                "/api/v1/verbs/nonexistent",
                "get_verb_by_infinitive",
                404,
                None,
                ["message"],
            ),
            (
                "/api/v1/verbs/nonexistent/conjugations",
                "get_verb_with_conjugations",
                404,
                None,
                ["message"],
            ),
        ],
    )
    def test_endpoint_responses(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        sample_verb,
        sample_verb_with_conjugations,
        endpoint,
        method_name,
        expected_status,
        return_value,
        expected_response_keys,
    ):
        """Test various endpoint responses with different scenarios."""
        # Resolve fixture references
        if return_value == "sample_verb":
            mock_return = sample_verb
        elif return_value == "sample_verb_with_conjugations":
            mock_return = sample_verb_with_conjugations
        else:
            mock_return = return_value

        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                getattr(mock_service, method_name).return_value = mock_return

                response = client.get(endpoint, headers=auth_headers)

                assert response.status_code == expected_status
                data = response.json()

                # Verify response structure
                for key in expected_response_keys:
                    assert key in data

                # Verify specific data for success cases
                if expected_status == 200 and mock_return:
                    if "infinitive" in expected_response_keys:
                        assert data["infinitive"] == "parler"
                    if "translation" in expected_response_keys:
                        assert data["translation"] == "to speak"

    @pytest.mark.parametrize(
        "endpoint,params,expected_service_call",
        [
            # URL encoding tests
            (
                "/api/v1/verbs/être",
                {},
                {
                    "infinitive": "être",
                    "auxiliary": None,
                    "reflexive": None,
                    "target_language_code": "eng",
                },
            ),
            # Parameter parsing tests
            (
                "/api/v1/verbs/parler",
                {
                    "auxiliary": "avoir",
                    "reflexive": "true",
                    "target_language_code": "fra",
                },
                {
                    "infinitive": "parler",
                    "auxiliary": "avoir",
                    "reflexive": True,
                    "target_language_code": "fra",
                },
            ),
            # Default language test
            (
                "/api/v1/verbs/random",
                {},
                {"target_language_code": "eng"},
            ),
        ],
    )
    def test_parameter_handling(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        sample_verb,
        endpoint,
        params,
        expected_service_call,
    ):
        """Test parameter parsing and handling."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb
                mock_service.get_random_verb.return_value = sample_verb

                response = client.get(endpoint, headers=auth_headers, params=params)

                assert response.status_code == 200

                # Verify correct service method was called with expected parameters
                if "random" in endpoint:
                    mock_service.get_random_verb.assert_called_once_with(
                        **expected_service_call
                    )
                else:
                    mock_service.get_verb_by_infinitive.assert_called_once_with(
                        **expected_service_call
                    )

    @pytest.mark.parametrize(
        "bool_value,expected_bool",
        [
            ("true", True),
            ("True", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("0", False),
        ],
    )
    def test_boolean_parameter_parsing(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        sample_verb,
        bool_value,
        expected_bool,
    ):
        """Test boolean parameter parsing variations."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb

                response = client.get(
                    "/api/v1/verbs/parler",
                    headers=auth_headers,
                    params={"reflexive": bool_value},
                )

                assert response.status_code == 200
                mock_service.get_verb_by_infinitive.assert_called_once_with(
                    infinitive="parler",
                    auxiliary=None,
                    reflexive=expected_bool,
                    target_language_code="eng",
                )

    @pytest.mark.parametrize(
        "auxiliary_value",
        ["avoir", "etre"],
    )
    def test_enum_parameter_validation(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        sample_verb,
        auxiliary_value,
    ):
        """Test enum parameter validation."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_verb_by_infinitive.return_value = sample_verb

                response = client.get(
                    "/api/v1/verbs/parler",
                    headers=auth_headers,
                    params={"auxiliary": auxiliary_value},
                )

                # Should not return 422 (validation error)
                assert response.status_code == 200


class TestVerbsAPIDownload:
    """Test verb download functionality."""

    def test_download_verb_success(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test successful verb download."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.download_verb.return_value = sample_verb

                response = client.post(
                    "/api/v1/verbs/download",
                    headers=auth_headers,
                    json={"infinitive": "parler", "target_language_code": "eng"},
                )

                assert response.status_code == 201
                data = response.json()
                assert data["infinitive"] == "parler"
                assert data["translation"] == "to speak"

    @pytest.mark.parametrize(
        "request_body,expected_status,expected_error_key",
        [
            # Missing required field
            ({"target_language_code": "eng"}, 422, "infinitive"),
            # Invalid data type
            ({"infinitive": 123, "target_language_code": "eng"}, 422, "infinitive"),
            # Empty infinitive
            ({"infinitive": "", "target_language_code": "eng"}, 422, "infinitive"),
        ],
    )
    def test_download_verb_validation_errors(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        request_body,
        expected_status,
        expected_error_key,
    ):
        """Test download verb request validation."""
        with _mock_auth_middleware(mock_api_key_info):
            response = client.post(
                "/api/v1/verbs/download",
                headers=auth_headers,
                json=request_body,
            )

            assert response.status_code == expected_status
            data = response.json()
            assert "detail" in data
            # Check that the error mentions the problematic field
            error_str = str(data["detail"]).lower()
            assert expected_error_key in error_str

    def test_download_verb_already_exists(
        self, client: TestClient, auth_headers, mock_api_key_info, sample_verb
    ):
        """Test download when verb already exists - should return 201 as re-downloading is supported."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                # Re-downloading should succeed and return the verb
                mock_service.download_verb.return_value = sample_verb

                response = client.post(
                    "/api/v1/verbs/download",
                    headers=auth_headers,
                    json={"infinitive": "parler", "target_language_code": "eng"},
                )

                assert response.status_code == 201
                data = response.json()
                assert data["infinitive"] == "parler"
                assert data["translation"] == "to speak"


class TestVerbsAPIResponseFormats:
    """Test response format and serialization."""

    @pytest.mark.parametrize(
        "endpoint,expected_fields",
        [
            (
                "/api/v1/verbs/random",
                {
                    "id",
                    "infinitive",
                    "translation",
                    "auxiliary",
                    "reflexive",
                    "target_language_code",
                    "past_participle",
                    "present_participle",
                    "classification",
                    "is_irregular",
                    "can_have_cod",
                    "can_have_coi",
                    "created_at",
                    "updated_at",
                },
            ),
            (
                "/api/v1/verbs/parler/conjugations",
                {"id", "infinitive", "conjugations"},
            ),
        ],
    )
    def test_response_schema_completeness(
        self,
        client: TestClient,
        auth_headers,
        mock_api_key_info,
        sample_verb,
        sample_verb_with_conjugations,
        endpoint,
        expected_fields,
    ):
        """Test that responses contain all expected fields."""
        mock_return = (
            sample_verb_with_conjugations if "conjugations" in endpoint else sample_verb
        )
        method_name = (
            "get_verb_with_conjugations"
            if "conjugations" in endpoint
            else "get_random_verb"
        )

        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                getattr(mock_service, method_name).return_value = mock_return

                response = client.get(endpoint, headers=auth_headers)

                assert response.status_code == 200
                data = response.json()

                # Verify all expected fields are present
                assert expected_fields.issubset(set(data.keys()))

                # Verify data types for key fields
                assert isinstance(data["id"], str)
                assert isinstance(data["infinitive"], str)
                if "conjugations" in data:
                    assert isinstance(data["conjugations"], list)

    def test_error_response_format(
        self, client: TestClient, auth_headers, mock_api_key_info
    ):
        """Test that error responses follow consistent format."""
        with _mock_auth_middleware(mock_api_key_info):
            with patch("src.api.verbs.VerbService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_random_verb.return_value = None

                response = client.get("/api/v1/verbs/random", headers=auth_headers)

                assert response.status_code == 404
                data = response.json()

                # Verify error response structure
                required_error_fields = {"message"}
                assert required_error_fields.issubset(set(data.keys()))
                assert isinstance(data["message"], str)
                assert len(data["message"]) > 0
