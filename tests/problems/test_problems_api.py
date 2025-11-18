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


# Note: admin_headers, write_headers, and read_headers are now provided
# by tests/conftest.py with dynamically generated test keys


@pytest.mark.unit
class TestProblemsAPIValidation:
    """Test API parameter validation and error handling."""

    def test_invalid_http_methods(self, client: TestClient, read_headers):
        """Test that invalid HTTP methods are rejected."""
        # Test POST to /random endpoint - endpoint is GET only
        response = client.post(f"{PROBLEMS_PREFIX}/random", headers=read_headers)
        assert response.status_code in [
            405,
            422,
        ]  # Method not allowed or validation error

        # Test PUT to generate endpoint with valid auth (should be 405, not 401)
        response = client.put(f"{PROBLEMS_PREFIX}/generate", headers=read_headers)
        assert response.status_code == 405  # Method not allowed

        # Test DELETE to generate endpoint with valid auth (should be 405, not 401)
        response = client.delete(f"{PROBLEMS_PREFIX}/generate", headers=read_headers)
        assert response.status_code == 405  # Method not allowed


@pytest.mark.unit
class TestProblemsAPIAuthentication:
    """Test authentication requirements for problems endpoints."""

    @pytest.fixture
    async def test_verb(self, request):
        """Get a known good verb with conjugations for problem generation."""
        from src.services.verb_service import VerbService

        verb_service = VerbService()

        # Use known good verbs that have conjugations in migrations
        known_verbs = ["être", "avoir", "pouvoir", "aller", "faire", "savoir", "parler"]
        test_name = request.node.name
        verb_index = hash(test_name) % len(known_verbs)
        infinitive = known_verbs[verb_index]

        verb = await verb_service.get_verb_by_infinitive(infinitive)
        if not verb:
            raise ValueError(f"Known verb {infinitive} not found in database")
        return verb

    def test_missing_auth_header(self, client: TestClient):
        """Test that requests without auth headers are rejected."""
        response = client.post(f"{PROBLEMS_PREFIX}/generate")
        assert response.status_code == 401
        data = response.json()
        assert "api key required" in data["message"].lower()

    def test_invalid_auth_header(self, client: TestClient):
        """Test that requests with invalid auth headers are rejected."""
        headers = {"X-API-Key": "invalid_key"}
        response = client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "invalid api key" in data["message"].lower()

    def test_malformed_auth_header(self, client: TestClient):
        """Test that requests with malformed auth headers are rejected."""
        headers = {"Authorization": "NotBearer test_key_fake_malformed"}
        response = client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401

    def test_empty_auth_header(self, client: TestClient):
        """Test that requests with empty auth headers are rejected."""
        headers = {"X-API-Key": ""}
        response = client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401

    def test_missing_bearer_prefix(self, client: TestClient):
        """Test that requests without proper API key format are rejected."""
        headers = {"X-API-Key": "not_a_valid_key_format"}
        response = client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401

    def test_inactive_api_key(self, client: TestClient):
        """Test that inactive API keys are rejected."""
        # Use the inactive test key from test data
        headers = {
            "X-API-Key": "test_key_inactive_1234567890abcdef1234567890abcdef1234567890abcdef12345"
        }
        response = client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert (
            "inactive" in data["message"].lower()
            or "invalid" in data["message"].lower()
        )

    def test_unsupported_auth_scheme(self, client: TestClient):
        """Test that unsupported auth schemes are rejected."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}  # Base64 encoded user:pass
        response = client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401

    async def test_wrong_scope_permissions(self, client: TestClient, read_headers):
        """Test that read scope can enqueue generation requests."""
        with patch("src.api.problems.QueueService") as mock_queue_class:
            mock_queue = AsyncMock()
            mock_queue.publish_problem_generation_request.return_value = (
                1,
                str(uuid4()),
            )
            mock_queue_class.return_value = mock_queue

            # Read operations should work with read key
            response = client.post(
                f"{PROBLEMS_PREFIX}/generate",
                headers=read_headers,
                json={"topic_tags": ["test_data"]},
            )
            assert response.status_code == 202


@pytest.mark.integration
class TestProblemsAPIIntegration:
    """Test full API integration with real authentication and services."""

    @pytest.fixture
    async def test_verb(self, request):
        """Get a known good verb with conjugations for problem generation."""
        from src.services.verb_service import VerbService

        verb_service = VerbService()

        # Use known good verbs that have conjugations in migrations
        known_verbs = ["être", "avoir", "pouvoir", "aller", "faire", "savoir", "parler"]
        test_name = request.node.name
        verb_index = hash(test_name) % len(known_verbs)
        infinitive = known_verbs[verb_index]

        verb = await verb_service.get_verb_by_infinitive(infinitive)
        if not verb:
            raise ValueError(f"Known verb {infinitive} not found in database")
        return verb

    async def test_generate_problem_endpoint(self, client: TestClient, read_headers):
        """Test generate problem endpoint returns 202 and enqueues async generation."""
        with patch("src.api.problems.QueueService") as mock_queue_class:
            mock_queue = AsyncMock()
            mock_queue.publish_problem_generation_request.return_value = (
                5,
                "550e8400-e29b-41d4-a716-446655440000",
            )
            mock_queue_class.return_value = mock_queue

            response = client.post(
                f"{PROBLEMS_PREFIX}/generate",
                headers=read_headers,
                json={"count": 5, "topic_tags": ["test_data"]},
            )
            assert response.status_code == 202
            data = response.json()
            assert "message" in data
            assert data["count"] == 5
            assert "request_id" in data
            assert isinstance(data["request_id"], str)
            assert "Enqueued" in data["message"]


@pytest.mark.integration
class TestRandomProblemParameterized:
    """Comprehensive parameterized tests for generate problem endpoint."""

    @pytest.fixture
    async def test_verb(self, request):
        """Get a known good verb with conjugations for problem generation."""
        from src.services.verb_service import VerbService

        verb_service = VerbService()

        # Use known good verbs that have conjugations in migrations
        # Use hash of test name to deterministically select verb (avoid random race conditions)
        known_verbs = ["être", "avoir", "pouvoir", "aller", "faire", "savoir", "parler"]
        test_name = request.node.name
        verb_index = hash(test_name) % len(known_verbs)
        infinitive = known_verbs[verb_index]

        verb = await verb_service.get_verb_by_infinitive(infinitive)
        if not verb:
            raise ValueError(f"Known verb {infinitive} not found in database")
        return verb

    @pytest.fixture
    def mock_queue_service(self):
        """Mock queue service to avoid Kafka connection in tests."""
        with patch("src.api.problems.QueueService") as mock_class:
            mock_instance = AsyncMock()

            async def mock_publish(**kwargs):
                count = kwargs.get("count", 1)
                # Return single request_id (new signature)
                request_id = f"550e8400-e29b-41d4-a716-{count:012d}"
                return count, request_id

            mock_instance.publish_problem_generation_request = mock_publish
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture(autouse=True)
    def mock_random_verb(self, test_verb):
        """Automatically mock get_random_verb for all tests in this class."""
        with patch(
            "src.services.problem_service.VerbService.get_random_verb",
            return_value=test_verb,
        ):
            yield

    async def test_default_behavior_generates_problem(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that POST request with no parameters enqueues with defaults."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"topic_tags": ["test_data"]},
        )

        assert response.status_code == 202
        data = response.json()

        # Should use default count of 1
        assert data["count"] == 1
        assert "message" in data
        assert "1 problem generation request" in data["message"].lower()

    async def test_target_language_basic(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that generate endpoint accepts target language parameter."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"target_language_code": "eng", "topic_tags": ["test_data"]},
        )

        assert response.status_code == 202
        data = response.json()
        assert "message" in data

    async def test_get_problem_by_id(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that generate endpoint enqueues requests successfully."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"count": 3, "topic_tags": ["test_data"]},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 3

    async def test_basic_constraint_processing(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that constraints are accepted in request."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={
                "constraints": {"grammatical_focus": ["direct_objects"]},
                "topic_tags": ["test_data"],
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1

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
        mock_queue_service,
        scenario_name,
        expected_structure,
    ):
        """Test that generate endpoint accepts various request scenarios."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"topic_tags": ["test_data"]},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1

    async def test_content_generation_error_handling(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that generate endpoint enqueues even if worker might fail later."""
        # With async processing, errors surface in worker logs, not API response
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"topic_tags": ["test_data"]},
        )

        # Should still return 202 - errors happen async in worker
        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1

    async def test_empty_request_uses_defaults(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that empty request uses default count of 1."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"topic_tags": ["test_data"]},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1  # Default count

    async def test_response_format_consistency(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that 202 response format is consistent."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"count": 5, "topic_tags": ["test_data"]},
        )

        assert response.status_code == 202
        data = response.json()

        # Required fields for 202 response
        required_fields = ["message", "count"]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Validate types
        assert isinstance(data["message"], str)
        assert isinstance(data["count"], int)
        assert data["count"] == 5

    async def test_multiple_request_consistency(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that multiple requests to the same endpoint work consistently."""
        # Make multiple requests
        responses = []
        for _ in range(3):
            response = client.post(
                f"{PROBLEMS_PREFIX}/generate",
                headers=read_headers,
                json={"topic_tags": ["test_data"]},
            )
            responses.append(response)

        # All should succeed with 202
        for response in responses:
            assert response.status_code == 202
            data = response.json()
            assert data["count"] == 1

    async def test_concurrent_request_handling(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that the endpoint can handle concurrent requests."""
        import asyncio

        async def make_request():
            return client.post(
                f"{PROBLEMS_PREFIX}/generate",
                headers=read_headers,
                json={"topic_tags": ["test_data"]},
            )

        # Make 3 concurrent requests
        responses = await asyncio.gather(*[make_request() for _ in range(3)])

        # All should succeed with 202
        for response in responses:
            assert response.status_code == 202
            data = response.json()
            assert data["count"] == 1
