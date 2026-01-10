"""API contract tests for problems endpoints.

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

from src.api.problems import API_PREFIX, get_queue_service
from src.main import ROUTER_PREFIX, app

PROBLEMS_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


# =============================================================================
# Test Client Fixtures with Dependency Overrides
# =============================================================================


@pytest.fixture
def client(monkeypatch):
    """Create a test client with auth disabled and services mocked."""
    from src.core.config import reset_settings
    from src.core.dependencies import get_problem_service
    from tests.api.conftest import MockProblemService, MockQueueService

    # Disable auth for contract testing
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    reset_settings()

    mock_problem_service = MockProblemService()
    mock_queue_service = MockQueueService()

    app.dependency_overrides[get_problem_service] = lambda: mock_problem_service
    app.dependency_overrides[get_queue_service] = lambda: mock_queue_service

    yield TestClient(app), mock_queue_service

    app.dependency_overrides.clear()
    reset_settings()


@pytest.fixture
def auth_client():
    """Create a test client with real auth enabled for auth tests."""
    return TestClient(app)


# =============================================================================
# Authentication Tests - Use real auth middleware
# =============================================================================


@pytest.mark.security
class TestProblemsAPIAuthentication:
    """Test authentication requirements for problems endpoints."""

    def test_missing_auth_header(self, auth_client: TestClient):
        """Test that requests without auth headers are rejected."""
        response = auth_client.post(f"{PROBLEMS_PREFIX}/generate")
        assert response.status_code == 401
        data = response.json()
        assert "api key required" in data["message"].lower()

    def test_invalid_auth_header(self, auth_client: TestClient):
        """Test that requests with invalid auth headers are rejected."""
        headers = {"X-API-Key": "invalid_key"}
        response = auth_client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert "invalid api key" in data["message"].lower()

    def test_malformed_auth_header(self, auth_client: TestClient):
        """Test that requests with malformed auth headers are rejected."""
        headers = {"Authorization": "NotBearer test_key_fake_malformed"}
        response = auth_client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401

    def test_empty_auth_header(self, auth_client: TestClient):
        """Test that requests with empty auth headers are rejected."""
        headers = {"X-API-Key": ""}
        response = auth_client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401

    def test_unsupported_auth_scheme(self, auth_client: TestClient):
        """Test that unsupported auth schemes are rejected."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        response = auth_client.post(f"{PROBLEMS_PREFIX}/generate", headers=headers)
        assert response.status_code == 401

    def test_random_endpoint_requires_auth(self, auth_client: TestClient):
        """Test that random endpoint requires authentication."""
        response = auth_client.get(f"{PROBLEMS_PREFIX}/random")
        assert response.status_code == 401
        data = response.json()
        assert "api key required" in data["message"].lower()


# =============================================================================
# Validation Tests - Mock services, test parameter validation
# =============================================================================


@pytest.mark.unit
class TestProblemsAPIValidation:
    """Test API parameter validation and error handling."""

    def test_invalid_http_methods(self, client):
        """Test that invalid HTTP methods are rejected."""
        test_client, _ = client

        response = test_client.post(f"{PROBLEMS_PREFIX}/random")
        assert response.status_code in [405, 422]

        response = test_client.put(f"{PROBLEMS_PREFIX}/generate")
        assert response.status_code == 405

        response = test_client.delete(f"{PROBLEMS_PREFIX}/generate")
        assert response.status_code == 405

    def test_invalid_topic_tags_type(self, client):
        """Test that invalid topic_tags type is rejected."""
        test_client, _ = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={"topic_tags": "not_a_list"},
        )
        assert response.status_code == 422


# =============================================================================
# Contract Tests - Mock services, test HTTP behavior
# =============================================================================


@pytest.mark.integration
class TestProblemsAPIContracts:
    """Test API contracts with mocked services."""

    def test_generate_problem_endpoint(self, client):
        """Test generate problem endpoint returns 202 and enqueues async generation."""
        test_client, mock_queue = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={"count": 5, "topic_tags": ["test_data"]},
        )
        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert data["count"] == 5
        assert "request_id" in data
        assert isinstance(data["request_id"], str)
        assert "Enqueued" in data["message"]

    def test_generate_default_count(self, client):
        """Test that empty request uses default count of 1."""
        test_client, _ = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={"topic_tags": ["test_data"]},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1
        assert "1 problem generation request" in data["message"].lower()

    def test_generate_with_target_language(self, client):
        """Test that generate endpoint accepts target language parameter."""
        test_client, _ = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={"target_language_code": "eng", "topic_tags": ["test_data"]},
        )
        assert response.status_code == 202
        data = response.json()
        assert "message" in data

    def test_generate_with_constraints(self, client):
        """Test that constraints are accepted in request."""
        test_client, mock_queue = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={
                "constraints": {"grammatical_focus": ["direct_objects"]},
                "topic_tags": ["test_data"],
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1
        assert len(mock_queue.published_requests) == 1
        assert mock_queue.published_requests[0]["constraints"] is not None

    def test_response_format_consistency(self, client):
        """Test that 202 response format is consistent."""
        test_client, _ = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={"count": 5, "topic_tags": ["test_data"]},
        )
        assert response.status_code == 202
        data = response.json()

        required_fields = ["message", "count"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        assert isinstance(data["message"], str)
        assert isinstance(data["count"], int)
        assert data["count"] == 5

    def test_random_problem_not_found(self, client):
        """Test random problem endpoint returns 404 if no problems exist."""
        test_client, _ = client

        response = test_client.get(f"{PROBLEMS_PREFIX}/random")
        assert response.status_code == 404
        assert "no problems available" in response.json()["message"].lower()

    def test_get_problem_by_id_not_found(self, client):
        """Test get problem by ID returns 404 for non-existent problem."""
        test_client, _ = client

        non_existent_id = uuid4()
        response = test_client.get(f"{PROBLEMS_PREFIX}/{non_existent_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()


# =============================================================================
# Topic Tags Contract Tests
# =============================================================================


@pytest.mark.integration
class TestTopicTagsContracts:
    """Test topic_tags functionality in problem generation API contracts."""

    def test_topic_tags_passed_to_queue(self, client):
        """Test that topic_tags are passed to queue service."""
        test_client, mock_queue = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={"topic_tags": ["test_data", "custom_tag", "advanced"]},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1
        assert len(mock_queue.published_requests) == 1
        assert mock_queue.published_requests[0]["topic_tags"] == [
            "test_data",
            "custom_tag",
            "advanced",
        ]

    def test_topic_tags_with_constraints(self, client):
        """Test topic_tags alongside problem generation constraints."""
        test_client, mock_queue = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={
                "constraints": {
                    "grammatical_focus": ["negation"],
                    "includes_negation": True,
                },
                "statement_count": 6,
                "topic_tags": ["test_data", "negation_test"],
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1
        assert len(mock_queue.published_requests) == 1
        request = mock_queue.published_requests[0]
        assert request["topic_tags"] == ["test_data", "negation_test"]
        assert request["statement_count"] == 6
        assert request["constraints"] is not None

    def test_topic_tags_with_special_characters(self, client):
        """Test that topic_tags with special characters are accepted."""
        test_client, _ = client

        response = test_client.post(
            f"{PROBLEMS_PREFIX}/generate",
            json={
                "topic_tags": [
                    "test_data",
                    "special-chars",
                    "tag_with_underscore",
                    "tag.with.dots",
                ]
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1


# =============================================================================
# Focus Filter Contract Tests
# =============================================================================


@pytest.mark.integration
class TestFocusFilterContracts:
    """Test focus filter parameter on random problem endpoint."""

    def test_random_with_focus_parameter_accepted(self, client):
        """Test that focus parameter is accepted on random endpoint."""
        test_client, _ = client

        # Focus parameter should be accepted (even if no problems match)
        response = test_client.get(f"{PROBLEMS_PREFIX}/random?focus=conjugation")
        # Will be 404 because mock has no problems, but param is accepted
        assert response.status_code == 404

        response = test_client.get(f"{PROBLEMS_PREFIX}/random?focus=pronouns")
        assert response.status_code == 404

    def test_random_with_invalid_focus_rejected(self, client):
        """Test that invalid focus values are rejected with 422."""
        test_client, _ = client

        response = test_client.get(f"{PROBLEMS_PREFIX}/random?focus=invalid_focus")
        assert response.status_code == 422
        data = response.json()
        # Validation error should mention the invalid value
        assert "detail" in data or "message" in data

    def test_random_with_focus_returns_filtered_problem(self, client):
        """Test that focus filter returns matching problems when available."""
        from datetime import UTC, datetime

        from src.schemas.problems import Problem, ProblemType

        test_client, _ = client

        # Add a problem to the mock service
        from src.core.dependencies import get_problem_service

        mock_service = app.dependency_overrides[get_problem_service]()
        problem_id = uuid4()
        mock_service.problems[problem_id] = Problem(
            id=problem_id,
            problem_type=ProblemType.GRAMMAR,
            title="Test Conjugation Problem",
            instructions="Choose correctly",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[{"content": "Test", "is_correct": True, "translation": "Test"}],
            topic_tags=["test_data"],
            metadata={"grammatical_focus": ["conjugation"]},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        response = test_client.get(f"{PROBLEMS_PREFIX}/random?focus=conjugation")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(problem_id)

    def test_random_without_focus_still_works(self, client):
        """Test that random endpoint works without focus parameter."""
        from datetime import UTC, datetime

        from src.schemas.problems import Problem, ProblemType

        test_client, _ = client

        # Add a problem
        from src.core.dependencies import get_problem_service

        mock_service = app.dependency_overrides[get_problem_service]()
        problem_id = uuid4()
        mock_service.problems[problem_id] = Problem(
            id=problem_id,
            problem_type=ProblemType.GRAMMAR,
            title="Test Problem",
            instructions="Choose correctly",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[{"content": "Test", "is_correct": True, "translation": "Test"}],
            topic_tags=["test_data"],
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        response = test_client.get(f"{PROBLEMS_PREFIX}/random")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
