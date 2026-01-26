"""Tests for generation requests API endpoints."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import ROUTER_PREFIX, app
from src.repositories.generation_requests_repository import (
    GenerationRequestRepository,
)
from src.repositories.problem_repository import ProblemRepository
from src.schemas.generation_requests import (
    EntityType,
    GenerationRequestCreate,
)
from src.schemas.problems import ProblemCreate, ProblemType

GEN_REQUESTS_PREFIX = f"{ROUTER_PREFIX}/generation-requests"


@pytest.fixture
def client(test_client_with_lifespan):
    """Provide a test client for the FastAPI app with lifespan run."""
    return test_client_with_lifespan


@pytest.mark.integration
class TestGenerationRequestsAPI:
    """Test suite for generation requests API."""

    @pytest.fixture
    async def test_generation_request_empty(self, test_supabase_client):
        """Create a generation request without problems for testing."""
        gen_repo = GenerationRequestRepository(test_supabase_client)

        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=5,
            metadata={"topic_tags": ["test_data"]},
        )
        return await gen_repo.create_generation_request(request_create)

    @pytest.mark.asyncio
    async def test_get_generation_request_success(
        self, client: TestClient, admin_headers, test_supabase_client
    ):
        """Test GET /generation-requests/{id} returns 200 with data."""
        gen_repo = GenerationRequestRepository(test_supabase_client)
        prob_repo = ProblemRepository(test_supabase_client)

        # Create a generation request with test_data tag
        # Test data is protected from expiration by skip_test_data=True in expire_stale_pending_requests
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=2,
            metadata={"topic_tags": ["test_data"]},
        )
        gen_request = await gen_repo.create_generation_request(request_create)
        assert gen_request.status.value == "pending"

        # Create associated problems
        for i in range(2):
            problem = ProblemCreate(
                problem_type=ProblemType.GRAMMAR,
                title=f"API Test {uuid4().hex[:8]}",
                instructions="Choose.",
                correct_answer_index=0,
                statements=[
                    {
                        "content": f"Content {i}.",
                        "is_correct": True,
                        "translation": "Trans.",
                    },
                    {
                        "content": f"Wrong {i}.",
                        "is_correct": False,
                        "explanation": "Bad",
                    },
                ],
                topic_tags=["test_data"],
                generation_request_id=gen_request.id,
            )
            await prob_repo.create_problem(problem)

        response = client.get(
            f"{GEN_REQUESTS_PREFIX}/{gen_request.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == str(gen_request.id)
        assert data["entity_type"] == "problem"
        assert data["status"] == "pending"
        assert data["requested_count"] == 2
        assert data["generated_count"] == 0
        assert len(data["entities"]) == 2

    def test_get_generation_request_empty_entities(
        self, client: TestClient, read_headers, test_generation_request_empty
    ):
        """Test GET with no problems returns empty entities array."""
        gen_request = test_generation_request_empty

        response = client.get(
            f"{GEN_REQUESTS_PREFIX}/{gen_request.id}",
            headers=read_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == str(gen_request.id)
        assert data["requested_count"] == 5
        assert data["generated_count"] == 0
        assert len(data["entities"]) == 0

    def test_get_generation_request_not_found(self, client: TestClient, admin_headers):
        """Test GET with invalid ID returns 404."""
        response = client.get(
            f"{GEN_REQUESTS_PREFIX}/{uuid4()}",
            headers=admin_headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert "message" in data
        assert "not found" in data["message"].lower()

    def test_get_generation_request_response_structure(
        self, client: TestClient, admin_headers, test_generation_request_empty
    ):
        """Test response has all required fields."""
        gen_request = test_generation_request_empty

        response = client.get(
            f"{GEN_REQUESTS_PREFIX}/{gen_request.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        assert "request_id" in data
        assert "entity_type" in data
        assert "status" in data
        assert "requested_count" in data
        assert "generated_count" in data
        assert "failed_count" in data
        assert "requested_at" in data
        assert "constraints" in data
        assert "error_message" in data
        assert "entities" in data

        # Verify types
        assert isinstance(data["entities"], list)
        assert isinstance(data["generated_count"], int)
        assert isinstance(data["failed_count"], int)
        # constraints can be None or dict
        assert data["constraints"] is None or isinstance(data["constraints"], dict)

    def test_get_generation_request_requires_auth(self, client: TestClient):
        """Test that endpoint requires authentication."""
        response = client.get(
            f"{GEN_REQUESTS_PREFIX}/{uuid4()}",
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True

    def test_get_generation_request_read_permission_allowed(
        self, client: TestClient, read_headers, test_generation_request_empty
    ):
        """Test that read permission can access generation requests."""
        gen_request = test_generation_request_empty

        response = client.get(
            f"{GEN_REQUESTS_PREFIX}/{gen_request.id}",
            headers=read_headers,
        )

        assert response.status_code == 200
