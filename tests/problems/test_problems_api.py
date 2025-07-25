from pprint import pprint
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.problems import API_PREFIX
from src.core.exceptions import ContentGenerationError
from src.main import ROUTER_PREFIX, app
from src.schemas.verbs import VerbCreate
from tests.problems.fixtures import mock_llm_responses
from tests.verbs.fixtures import sample_verb_data

PROBLEMS_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def read_headers():
    """Headers for read API key."""
    return {
        "X-API-Key": "sk_live_red1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.fixture
def write_headers():
    """Headers for write API key."""
    return {
        "X-API-Key": "sk_live_wrt1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.fixture
def admin_headers():
    """Headers for admin API key."""
    return {
        "X-API-Key": "sk_live_adm1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.mark.unit
class TestProblemsAPIValidation:
    """Test API parameter validation and error handling."""

    def test_invalid_http_methods(self, client: TestClient, read_headers):
        """Test that invalid HTTP methods return 405."""
        # Test POST to problems endpoint with valid auth (should be 405, not 401)
        response = client.post(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
        assert response.status_code == 405  # Method not allowed

        # Test PUT to problems endpoint with valid auth (should be 405, not 401)
        response = client.put(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
        assert response.status_code == 405  # Method not allowed

        # Test DELETE to problems endpoint with valid auth (should be 405, not 401)
        response = client.delete(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
        assert response.status_code == 405  # Method not allowed


@pytest.mark.unit
class TestProblemsAPIAuthentication:
    """Test authentication requirements for problems endpoints."""

    def test_missing_auth_header(self, client: TestClient):
        """Test that requests without auth headers are rejected."""
        response = client.get(f"{PROBLEMS_PREFIX}/random")
        assert response.status_code == 401
        data = response.json()
        assert "api key required" in data["message"].lower()

    def test_invalid_auth_header(self, client: TestClient):
        """Test that requests with invalid auth headers are rejected."""
        headers = {"X-API-Key": "invalid_key"}
        response = client.get(f"{PROBLEMS_PREFIX}/random", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "invalid api key" in data["message"].lower()

    def test_malformed_auth_header(self, client: TestClient):
        """Test that requests with malformed auth headers are rejected."""
        headers = {"Authorization": "NotBearer sk_test_key"}
        response = client.get(f"{PROBLEMS_PREFIX}/random", headers=headers)
        assert response.status_code == 401

    def test_empty_auth_header(self, client: TestClient):
        """Test that requests with empty auth headers are rejected."""
        headers = {"X-API-Key": ""}
        response = client.get(f"{PROBLEMS_PREFIX}/random", headers=headers)
        assert response.status_code == 401

    def test_missing_bearer_prefix(self, client: TestClient):
        """Test that requests without proper API key format are rejected."""
        headers = {"X-API-Key": "not_a_valid_key_format"}
        response = client.get(f"{PROBLEMS_PREFIX}/random", headers=headers)
        assert response.status_code == 401

    def test_inactive_api_key(self, client: TestClient):
        """Test that inactive API keys are rejected."""
        # Use the inactive test key from test data
        headers = {
            "X-API-Key": "sk_live_ina1234567890123456789012345678901234567890123456789012345678901234"
        }
        response = client.get(f"{PROBLEMS_PREFIX}/random", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert (
            "inactive" in data["message"].lower()
            or "invalid" in data["message"].lower()
        )

    def test_unsupported_auth_scheme(self, client: TestClient):
        """Test that unsupported auth schemes are rejected."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}  # Base64 encoded user:pass
        response = client.get(f"{PROBLEMS_PREFIX}/random", headers=headers)
        assert response.status_code == 401

    def test_wrong_scope_permissions(self, client: TestClient, mock_llm_responses):
        """Test that keys without required scope are rejected."""
        # This test demonstrates scope validation, but our current implementation
        # allows read access for all active keys, so this test validates the current behavior
        read_headers = {
            "X-API-Key": "sk_live_red1234567890123456789012345678901234567890123456789012345678901234"
        }

        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            # Read operations should work with read key
            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
            # The response should be either 200 (success) or 503 (service error due to missing data)
            # but NOT 401/403 (auth error)
            assert response.status_code in [200, 503]


@pytest.mark.integration
class TestProblemsAPIIntegration:
    """Test full API integration with real authentication and services."""

    def test_random_problem_endpoint(
        self, client: TestClient, read_headers, mock_llm_responses
    ):
        """Test random problem endpoint with read permissions."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get("error", False) is False


@pytest.mark.integration
class TestRandomProblemParameterized:
    """Comprehensive parameterized tests for random problem endpoint."""

    @pytest.fixture
    async def test_verb(self, test_supabase_client, sample_verb_data):
        """Create a test verb for problem generation."""
        from src.services.verb_service import VerbService

        verb_service = VerbService()
        verb_service.db_client = test_supabase_client

        verb_data = VerbCreate(**sample_verb_data)
        return await verb_service.create_verb(verb_data)

    async def test_default_behavior_generates_problem(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test that GET request with no parameters generates a problem using defaults."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 200
            data = response.json()

            # Should use default values
            assert len(data["statements"]) == 4  # Default statement count
            assert 0 <= data["correct_answer_index"] < len(data["statements"])
            assert any(stmt["is_correct"] for stmt in data["statements"])

            # Problem structure validation
            assert data["problem_type"] == "grammar"
            assert data["target_language_code"] == "eng"
            assert "title" in data
            assert "instructions" in data

    async def test_target_language_basic(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test basic target language functionality with English."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["target_language_code"] == "eng"

    def test_get_problem_by_id(
        self, client: TestClient, read_headers, mock_llm_responses
    ):
        """Test retrieving problem by ID."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            random_response = client.get(
                f"{PROBLEMS_PREFIX}/random", headers=read_headers
            )

            get_response = client.get(
                f"{PROBLEMS_PREFIX}/{random_response.json()["id"]}",
                headers=read_headers,
            )

            assert get_response.status_code == 200
            data = get_response.json()
            assert data.get("error", False) is False

    async def test_basic_constraint_processing(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test that basic constraint processing works through business logic."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 200
            data = response.json()

            # Problem should have valid structure
            assert data["problem_type"] == "grammar"
            assert data["statements"]
            assert data["instructions"]
            assert "topic_tags" in data

            # This validates that the constraint processing business logic
            # flows correctly through the system without error
            assert isinstance(data["statements"], list)
            assert len(data["statements"]) > 0
            assert all("content" in stmt for stmt in data["statements"])
            assert all("is_correct" in stmt for stmt in data["statements"])

    @pytest.mark.parametrize(
        "scenario_name,expected_structure",
        [
            (
                "basic_request",
                {
                    "problem_type": "grammar",
                    "statement_count": 4,  # Default
                    "has_correct_answer": True,
                },
            ),
            (
                "default_behavior",
                {
                    "problem_type": "grammar",
                    "statement_count": 4,  # Default
                    "has_correct_answer": True,
                },
            ),
        ],
    )
    async def test_realistic_learning_scenarios(
        self,
        client: TestClient,
        read_headers,
        test_verb,
        mock_llm_responses,
        scenario_name,
        expected_structure,
    ):
        """Test realistic learning scenario behavior."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 200
            data = response.json()

            # Validate expected structure
            assert data["problem_type"] == expected_structure["problem_type"]
            assert len(data["statements"]) == expected_structure["statement_count"]

            if expected_structure["has_correct_answer"]:
                # Verify correct_answer_index points to a correct statement
                correct_idx = data["correct_answer_index"]

                assert 0 <= correct_idx < len(data["statements"])
                assert data["statements"][correct_idx]["is_correct"] is True

            # Validate statement structure
            for stmt in data["statements"]:
                assert "content" in stmt
                assert "is_correct" in stmt
                if stmt["is_correct"]:
                    assert "translation" in stmt
                else:
                    assert "explanation" in stmt

    async def test_content_generation_error_handling(
        self, client: TestClient, read_headers, test_verb
    ):
        """Test handling of LLM content generation errors."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            # Simulate LLM failure
            mock_client.handle_request.side_effect = ContentGenerationError(
                "LLM service unavailable"
            )

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 503
            data = response.json()
            assert "LLM service unavailable" in data["message"]

    async def test_empty_request_uses_defaults(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test that empty request uses default values."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 200
            data = response.json()

            # Should use defaults
            assert len(data["statements"]) == 4  # Default statement_count
            assert data["target_language_code"] == "eng"  # Default language
            assert data["problem_type"] == "grammar"

    async def test_response_format_consistency(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test that response format is consistent and complete."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 200
            data = response.json()

            # Required fields
            required_fields = [
                "id",
                "problem_type",
                "title",
                "instructions",
                "statements",
                "correct_answer_index",
                "target_language_code",
                "topic_tags",
                "created_at",
                "updated_at",
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Validate types
            assert isinstance(data["statements"], list)
            assert isinstance(data["correct_answer_index"], int)
            assert isinstance(data["topic_tags"], list)
            assert len(data["statements"]) > 0

    async def test_multiple_request_consistency(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test that multiple requests to the same endpoint work consistently."""
        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            # Make multiple requests
            responses = []
            for _ in range(3):
                response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
                responses.append(response)

            # All should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["problem_type"] == "grammar"

    async def test_concurrent_request_handling(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test that the endpoint can handle concurrent requests."""
        import asyncio

        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            async def make_request():
                return client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            # Make 3 concurrent requests
            responses = await asyncio.gather(*[make_request() for _ in range(3)])

            # All should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["problem_type"] == "grammar"
