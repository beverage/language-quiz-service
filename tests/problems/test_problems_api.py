from pprint import pprint
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.problems import API_PREFIX
from src.core.exceptions import ContentGenerationError
from src.main import ROUTER_PREFIX, app
from src.schemas.verbs import VerbCreate
from tests.verbs.fixtures import sample_verb_data

PROBLEMS_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


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
class TestProblemsAPIAuthentication:
    """Test authentication requirements without mocking."""

    def test_endpoints_require_authentication(self, client: TestClient):
        """Test that all endpoints require authentication."""
        endpoints = [
            f"{PROBLEMS_PREFIX}/random",
            f"{PROBLEMS_PREFIX}/{uuid4()}",
            f"{PROBLEMS_PREFIX}/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            data = response.json()
            assert data["error"] is True
            assert "API key required" in data["message"]

    def test_get_random_problem_requires_authentication(self, client: TestClient):
        """Test that the random problem endpoint requires authentication."""
        response = client.get(f"{PROBLEMS_PREFIX}/random")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "API key required" in data["message"]

    def test_get_problem_by_id_requires_authentication(self, client: TestClient):
        """Test that the problem by id endpoint requires authentication."""
        response = client.get(f"{PROBLEMS_PREFIX}/{uuid4()}")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "API key required" in data["message"]


@pytest.mark.unit
class TestProblemsAPIValidation:
    """Test request validation with authenticated requests."""

    def test_invalid_uuid_format(self, client: TestClient, admin_headers):
        """Test validation with invalid UUID formats."""
        # Test invalid UUID in path
        response = client.get(f"{PROBLEMS_PREFIX}/not-a-uuid", headers=admin_headers)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_method_not_allowed(self, client: TestClient, admin_headers):
        """Test that unsupported HTTP methods are rejected."""
        # POST not supported on random endpoint
        response = client.post(f"{PROBLEMS_PREFIX}/random", headers=admin_headers)
        assert response.status_code == 405  # Method not allowed


@pytest.mark.integration
class TestProblemsAPIIntegration:
    """Test full API integration with real authentication and services."""

    def test_random_problem_endpoint(self, client: TestClient, read_headers):
        """Test random problem endpoint with read permissions."""
        response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("error", False) is False


@pytest.mark.integration
class TestRandomProblemParameterized:
    """Comprehensive parameterized tests for random problem endpoint."""

    @pytest.fixture
    async def mock_llm_responses(self):
        """Mock LLM responses for consistent testing."""
        import itertools

        # Mock sentence generation responses - enough variety for testing
        sentence_responses = [
            '{"sentence": "Je parle français.", "translation": "I speak French.", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
            '{"sentence": "Je parles français.", "translation": "", "is_correct": false, "explanation": "Wrong conjugation", "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
            '{"sentence": "Je ne parle pas français.", "translation": "I do not speak French.", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "pas"}',
            '{"sentence": "Je parle le français.", "translation": "I speak the French.", "is_correct": false, "explanation": "Incorrect article usage", "has_compliment_object_direct": true, "has_compliment_object_indirect": false, "direct_object": "masculine", "indirect_object": "none", "negation": "none"}',
            '{"sentence": "Tu parles bien.", "translation": "You speak well.", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
            '{"sentence": "Il parle mal.", "translation": "He speaks badly.", "is_correct": false, "explanation": "Poor grammar", "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
        ]
        # Return infinite cycle of responses to handle multiple LLM calls per test
        return itertools.cycle(sentence_responses)

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

            print(random_response.json())
            
            get_response = client.get(
                f"{PROBLEMS_PREFIX}/{random_response.json()["id"]}",
                headers=read_headers,
            )
            
            print(get_response.json())

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

    @pytest.mark.parametrize(
        "permission_headers,expected_status",
        [
            ("read_headers", 200),  # Read permission should work
            ("write_headers", 200),  # Write permission should work
            ("admin_headers", 200),  # Admin permission should work
            ("inactive_headers", 401),  # Inactive key should fail
        ],
    )
    async def test_authentication_matrix(
        self,
        client: TestClient,
        test_verb,
        mock_llm_responses,
        permission_headers,
        expected_status,
        request,
    ):
        """Test authentication across different permission levels."""
        headers = request.getfixturevalue(permission_headers)

        with patch("src.services.sentence_service.OpenAIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.handle_request.side_effect = mock_llm_responses

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=headers)

            assert response.status_code == expected_status

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

            print(pprint(data))

            if expected_structure["has_correct_answer"]:
                # Verify correct_answer_index points to a correct statement
                correct_idx = data["correct_answer_index"]

                print(correct_idx)

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
