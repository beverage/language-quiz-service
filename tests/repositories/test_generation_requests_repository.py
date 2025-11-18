"""Tests for GenerationRequestRepository."""

from uuid import uuid4

import pytest

from src.repositories.generation_requests_repository import (
    GenerationRequestRepository,
)
from src.repositories.problem_repository import ProblemRepository
from src.schemas.generation_requests import (
    EntityType,
    GenerationRequestCreate,
    GenerationStatus,
)
from src.schemas.problems import ProblemCreate, ProblemType


@pytest.mark.asyncio
class TestGenerationRequestRepository:
    """Test suite for GenerationRequestRepository."""

    async def test_create_generation_request(self, test_supabase_client):
        """Test creating a generation request."""
        repo = GenerationRequestRepository(test_supabase_client)

        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=5,
            status=GenerationStatus.PENDING,
            metadata={"topic_tags": ["test_data"]},
        )

        result = await repo.create_generation_request(request_create)

        assert result.id is not None
        assert result.entity_type == EntityType.PROBLEM
        assert result.status == GenerationStatus.PENDING
        assert result.requested_count == 5
        assert result.generated_count == 0
        assert result.failed_count == 0
        assert result.requested_at is not None
        assert result.started_at is None
        assert result.completed_at is None

    async def test_create_generation_request_with_constraints(
        self, test_supabase_client
    ):
        """Test creating a generation request with constraints."""
        repo = GenerationRequestRepository(test_supabase_client)

        constraints = {
            "includes_cod": True,
            "includes_negation": False,
            "tenses_used": ["present", "passe_compose"],
        }

        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=3,
            constraints=constraints,
            metadata={"statement_count": 4, "topic_tags": ["test_data"]},
        )

        result = await repo.create_generation_request(request_create)

        assert result.constraints == constraints
        assert result.metadata == {"statement_count": 4, "topic_tags": ["test_data"]}

    async def test_get_generation_request_by_id(self, test_supabase_client):
        """Test getting a generation request by ID."""
        repo = GenerationRequestRepository(test_supabase_client)

        # Create a request
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=2,
            metadata={"topic_tags": ["test_data"]},
        )
        created = await repo.create_generation_request(request_create)

        # Get it back
        result = await repo.get_generation_request(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.entity_type == EntityType.PROBLEM
        assert result.requested_count == 2

    async def test_get_generation_request_not_found(self, test_supabase_client):
        """Test getting a non-existent generation request returns None."""
        repo = GenerationRequestRepository(test_supabase_client)

        result = await repo.get_generation_request(uuid4())

        assert result is None

    async def test_get_problems_by_request_id_empty(self, test_supabase_client):
        """Test getting problems for a request with no problems."""
        repo = GenerationRequestRepository(test_supabase_client)

        # Create a request
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=5,
            metadata={"topic_tags": ["test_data"]},
        )
        created = await repo.create_generation_request(request_create)

        # Get problems (should be empty)
        problems = await repo.get_problems_by_request_id(created.id)

        assert problems == []

    async def test_get_problems_by_request_id_with_problems(self, test_supabase_client):
        """Test getting problems linked to a generation request."""
        gen_repo = GenerationRequestRepository(test_supabase_client)
        prob_repo = ProblemRepository(test_supabase_client)

        # Create a generation request
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=2,
            metadata={"topic_tags": ["test_data"]},
        )
        gen_request = await gen_repo.create_generation_request(request_create)

        # Create problems linked to this request
        for i in range(2):
            problem = ProblemCreate(
                problem_type=ProblemType.GRAMMAR,
                title=f"Test Problem {uuid4().hex[:8]}",
                instructions="Choose the correct sentence.",
                correct_answer_index=0,
                statements=[
                    {
                        "content": f"Je parle français {i}.",
                        "is_correct": True,
                        "translation": "I speak French.",
                    },
                    {
                        "content": f"Je parles français {i}.",
                        "is_correct": False,
                        "explanation": "Wrong conjugation",
                    },
                ],
                topic_tags=["test_data"],
                generation_request_id=gen_request.id,
            )
            await prob_repo.create_problem(problem)

        # Get problems by request ID
        problems = await gen_repo.get_problems_by_request_id(gen_request.id)

        assert len(problems) == 2
        assert all(p["generation_request_id"] == str(gen_request.id) for p in problems)

    async def test_get_problems_by_request_id_multiple(self, test_supabase_client):
        """Test multiple problems share the same generation_request_id."""
        gen_repo = GenerationRequestRepository(test_supabase_client)
        prob_repo = ProblemRepository(test_supabase_client)

        # Create a generation request
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=5,
            metadata={"topic_tags": ["test_data"]},
        )
        gen_request = await gen_repo.create_generation_request(request_create)

        # Create 5 problems with same generation_request_id
        problem_ids = []
        for i in range(5):
            problem = ProblemCreate(
                problem_type=ProblemType.GRAMMAR,
                title=f"Batch Problem {uuid4().hex[:8]}",
                instructions="Choose the correct sentence.",
                correct_answer_index=0,
                statements=[
                    {
                        "content": f"Sentence {i}.",
                        "is_correct": True,
                        "translation": f"Translation {i}.",
                    },
                    {
                        "content": f"Wrong {i}.",
                        "is_correct": False,
                        "explanation": "Wrong",
                    },
                ],
                topic_tags=["test_data"],
                generation_request_id=gen_request.id,
            )
            created = await prob_repo.create_problem(problem)
            problem_ids.append(created.id)

        # Get all problems
        problems = await gen_repo.get_problems_by_request_id(gen_request.id)

        assert len(problems) == 5
        retrieved_ids = {p["id"] for p in problems}
        assert retrieved_ids == set(str(pid) for pid in problem_ids)
