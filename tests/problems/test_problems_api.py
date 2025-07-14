"""Tests for problems API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import UUID

from src.main import app
from src.services.problem_service import ProblemService
from src.schemas.problems import Problem, ProblemType


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_problem_service():
    """Mock problem service for testing."""
    service = AsyncMock(spec=ProblemService)
    return service


@pytest.mark.functional
class TestProblemsAPI:
    """Test problems API endpoints."""

    def test_problems_router_exists(self, client: TestClient):
        """Test that the problems router is included in the app."""
        # Test that the router is registered by checking available routes
        routes = [route.path for route in app.routes]

        # Check that we have the problems prefix in our routes
        # Note: This tests the current placeholder structure
        problem_routes = [route for route in routes if "/problems" in route]
        assert len(problem_routes) >= 0  # At least the prefix exists

        # TODO: Update when endpoints are implemented
        # Expected routes:
        # - GET /api/v1/problems/ - List problems
        # - POST /api/v1/problems/ - Create problem
        # - GET /api/v1/problems/random - Random problem
        # - GET /api/v1/problems/{problem_id} - Get specific problem

    def test_problems_endpoints_not_implemented_yet(self, client: TestClient):
        """Test that problems endpoints return appropriate responses (placeholder behavior)."""
        # These tests document the current placeholder state
        # TODO: Update when actual endpoints are implemented

        # Test non-existent problem endpoints return 404
        response = client.get("/api/v1/problems/")
        assert response.status_code == 404

        response = client.get("/api/v1/problems/random")
        assert response.status_code == 404

        response = client.post("/api/v1/problems/")
        assert response.status_code == 404

        # Test with UUID
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/problems/{test_uuid}")
        assert response.status_code == 404

    # TODO: Implement these tests when endpoints are added
    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_problems_list(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/ endpoint."""
        mock_problem_service.get_problems.return_value = ([], 0)

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get("/api/v1/problems/")

        assert response.status_code == 200
        data = response.json()
        assert data["problems"] == []
        assert data["total"] == 0
        mock_problem_service.get_problems.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_random_problem(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/random endpoint."""
        # Mock a simple problem
        mock_problem = Problem(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            problem_type=ProblemType.GRAMMAR,
            title="Test Problem",
            instructions="Choose the correct answer",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                },
                {
                    "content": "Je parlons français.",
                    "is_correct": False,
                    "explanation": "Wrong conjugation",
                },
                {
                    "content": "Je parlez français.",
                    "is_correct": False,
                    "explanation": "Wrong conjugation",
                },
                {
                    "content": "Je parlent français.",
                    "is_correct": False,
                    "explanation": "Wrong conjugation",
                },
            ],
            topic_tags=["grammar", "conjugation"],
            source_statement_ids=[],
            metadata={},
        )

        mock_problem_service.create_random_grammar_problem.return_value = mock_problem

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get("/api/v1/problems/random")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Problem"
        assert data["problem_type"] == "grammar"
        assert len(data["statements"]) == 4
        mock_problem_service.create_random_grammar_problem.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_random_problem_with_constraints(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/random with query parameters."""
        mock_problem = Problem(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            problem_type=ProblemType.GRAMMAR,
            title="Test Problem",
            instructions="Choose the correct answer",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[],
            topic_tags=["grammar"],
            source_statement_ids=[],
            metadata={},
        )

        mock_problem_service.create_random_grammar_problem.return_value = mock_problem

        query_params = {
            "statement_count": 3,
            "include_cod": True,
            "include_coi": False,
            "include_negation": True,
            "tenses": ["present", "future_simple"],
        }

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get("/api/v1/problems/random", params=query_params)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Problem"

        # Verify the service was called with correct constraints
        mock_problem_service.create_random_grammar_problem.assert_called_once()
        call_args = mock_problem_service.create_random_grammar_problem.call_args
        assert call_args[1]["statement_count"] == 3

        constraints = call_args[1]["constraints"]
        assert constraints.includes_cod is True
        assert constraints.includes_coi is False
        assert constraints.includes_negation is True
        assert constraints.tenses_used == ["present", "future_simple"]

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_problem_by_id(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/{problem_id} endpoint."""
        mock_problem = Problem(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            problem_type=ProblemType.GRAMMAR,
            title="Test Problem",
            instructions="Choose the correct answer",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[],
            topic_tags=["grammar"],
            source_statement_ids=[],
            metadata={},
        )

        mock_problem_service.get_problem.return_value = mock_problem

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get(f"/api/v1/problems/{mock_problem.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Problem"
        mock_problem_service.get_problem.assert_called_once_with(mock_problem.id)

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_problem_by_id_not_found(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/{problem_id} endpoint when problem not found."""
        mock_problem_service.get_problem.return_value = None
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get(f"/api/v1/problems/{test_uuid}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_create_problem(self, client: TestClient, mock_problem_service: AsyncMock):
        """Test POST /api/v1/problems/ endpoint."""
        mock_problem = Problem(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            problem_type=ProblemType.GRAMMAR,
            title="Test Problem",
            instructions="Choose the correct answer",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[],
            topic_tags=["grammar"],
            source_statement_ids=[],
            metadata={},
        )

        mock_problem_service.create_problem.return_value = mock_problem

        request_data = {
            "problem_type": "grammar",
            "title": "Test Problem",
            "instructions": "Choose the correct answer",
            "correct_answer_index": 0,
            "target_language_code": "eng",
            "statements": [
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                },
                {
                    "content": "Je parlons français.",
                    "is_correct": False,
                    "explanation": "Wrong conjugation",
                },
            ],
            "topic_tags": ["grammar"],
            "source_statement_ids": [],
            "metadata": {},
        }

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.post("/api/v1/problems/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Problem"
        mock_problem_service.create_problem.assert_called_once()


@pytest.mark.functional
class TestProblemsAPIValidation:
    """Test input validation for problems API endpoints."""

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_invalid_uuid_format(self, client: TestClient):
        """Test that invalid UUID formats are rejected."""
        response = client.get("/api/v1/problems/invalid-uuid")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_random_problem_validation(self, client: TestClient):
        """Test validation for random problem endpoint."""
        # Test invalid statement count
        response = client.get("/api/v1/problems/random", params={"statement_count": 1})
        assert response.status_code == 422

        response = client.get("/api/v1/problems/random", params={"statement_count": 11})
        assert response.status_code == 422

        # Test invalid tense values
        response = client.get(
            "/api/v1/problems/random", params={"tenses": ["invalid_tense"]}
        )
        assert response.status_code == 422

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_create_problem_validation(self, client: TestClient):
        """Test validation for create problem endpoint."""
        # Test missing required fields
        response = client.post("/api/v1/problems/", json={})
        assert response.status_code == 422

        # Test invalid problem type
        response = client.post(
            "/api/v1/problems/",
            json={
                "problem_type": "invalid_type",
                "title": "Test Problem",
                "instructions": "Choose the correct answer",
                "correct_answer_index": 0,
                "target_language_code": "eng",
                "statements": [],
                "topic_tags": [],
                "source_statement_ids": [],
                "metadata": {},
            },
        )
        assert response.status_code == 422

        # Test invalid correct_answer_index
        response = client.post(
            "/api/v1/problems/",
            json={
                "problem_type": "grammar",
                "title": "Test Problem",
                "instructions": "Choose the correct answer",
                "correct_answer_index": 5,  # Out of bounds
                "target_language_code": "eng",
                "statements": [
                    {
                        "content": "Je parle français.",
                        "is_correct": True,
                        "translation": "I speak French.",
                    }
                ],
                "topic_tags": [],
                "source_statement_ids": [],
                "metadata": {},
            },
        )
        assert response.status_code == 422


@pytest.mark.functional
class TestProblemsAPIFiltering:
    """Test filtering and search functionality for problems API."""

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_get_problems_with_filters(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/ with query parameters."""
        mock_problem_service.get_problems.return_value = ([], 0)

        query_params = {
            "problem_type": "grammar",
            "topic_tags": ["conjugation", "negation"],
            "limit": 10,
            "offset": 0,
        }

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get("/api/v1/problems/", params=query_params)

        assert response.status_code == 200
        data = response.json()
        assert data["problems"] == []
        assert data["total"] == 0
        mock_problem_service.get_problems.assert_called_once()

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_search_problems_by_focus(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/search with grammatical focus."""
        mock_problem_service.get_problems_by_grammatical_focus.return_value = []

        query_params = {"focus": "direct_objects", "limit": 20}

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get("/api/v1/problems/search", params=query_params)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_problem_service.get_problems_by_grammatical_focus.assert_called_once_with(
            "direct_objects", 20
        )

    @pytest.mark.skip(reason="Endpoints not implemented yet")
    def test_search_problems_by_topic(
        self, client: TestClient, mock_problem_service: AsyncMock
    ):
        """Test GET /api/v1/problems/search with topic tags."""
        mock_problem_service.get_problems_by_topic.return_value = []

        query_params = {"topic_tags": ["grammar", "conjugation"], "limit": 15}

        with patch(
            "src.api.problems.ProblemService", return_value=mock_problem_service
        ):
            response = client.get("/api/v1/problems/search", params=query_params)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_problem_service.get_problems_by_topic.assert_called_once_with(
            ["grammar", "conjugation"], 15
        )
