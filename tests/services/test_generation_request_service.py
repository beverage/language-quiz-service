"""Tests for GenerationRequestService."""

from uuid import uuid4

import pytest

from src.core.exceptions import NotFoundError
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
from src.services.generation_request_service import GenerationRequestService


@pytest.mark.asyncio
class TestGenerationRequestService:
    """Test suite for GenerationRequestService."""

    async def test_get_generation_request_with_entities_found(
        self, test_supabase_client
    ):
        """Test getting a generation request with its associated problems."""
        # Create repositories
        gen_repo = GenerationRequestRepository(test_supabase_client)
        prob_repo = ProblemRepository(test_supabase_client)

        # Create a generation request
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=3,
            metadata={"topic_tags": ["test_data"]},
        )
        gen_request = await gen_repo.create_generation_request(request_create)

        # Create problems linked to this request
        from uuid import uuid4

        for i in range(3):
            problem = ProblemCreate(
                problem_type=ProblemType.GRAMMAR,
                title=f"Test Problem {uuid4().hex[:8]}",
                instructions="Choose the correct sentence.",
                correct_answer_index=0,
                statements=[
                    {
                        "content": f"Je parle {i}.",
                        "is_correct": True,
                        "translation": "I speak.",
                    },
                    {
                        "content": f"Je parles {i}.",
                        "is_correct": False,
                        "explanation": "Wrong",
                    },
                ],
                topic_tags=["test_data"],
                generation_request_id=gen_request.id,
            )
            await prob_repo.create_problem(problem)

        # Test service
        service = GenerationRequestService(gen_repo, prob_repo)
        (
            result_request,
            result_problems,
        ) = await service.get_generation_request_with_entities(gen_request.id)

        assert result_request.id == gen_request.id
        assert len(result_problems) == 3
        assert all(p.generation_request_id == gen_request.id for p in result_problems)

    async def test_get_generation_request_with_entities_no_problems(
        self, test_supabase_client
    ):
        """Test getting a generation request with no associated problems."""
        gen_repo = GenerationRequestRepository(test_supabase_client)
        prob_repo = ProblemRepository(test_supabase_client)

        # Create a generation request with no problems
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=5,
            status=GenerationStatus.PENDING,
            metadata={"topic_tags": ["test_data"]},
        )
        gen_request = await gen_repo.create_generation_request(request_create)

        # Test service
        service = GenerationRequestService(gen_repo, prob_repo)
        (
            result_request,
            result_problems,
        ) = await service.get_generation_request_with_entities(gen_request.id)

        assert result_request.id == gen_request.id
        assert result_request.status == GenerationStatus.PENDING
        assert len(result_problems) == 0

    async def test_get_generation_request_with_entities_not_found(
        self, test_supabase_client
    ):
        """Test getting a non-existent generation request raises NotFoundError."""
        gen_repo = GenerationRequestRepository(test_supabase_client)
        prob_repo = ProblemRepository(test_supabase_client)
        service = GenerationRequestService(gen_repo, prob_repo)

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_generation_request_with_entities(uuid4())

        assert "not found" in str(exc_info.value).lower()

    async def test_get_generation_request_with_entities_problem_type(
        self, test_supabase_client
    ):
        """Test that only problem entity types return problems."""
        gen_repo = GenerationRequestRepository(test_supabase_client)
        prob_repo = ProblemRepository(test_supabase_client)

        # Create a generation request with entity_type=problem
        request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=2,
            metadata={"topic_tags": ["test_data"]},
        )
        gen_request = await gen_repo.create_generation_request(request_create)

        # Create problems
        from uuid import uuid4

        for i in range(2):
            problem = ProblemCreate(
                problem_type=ProblemType.GRAMMAR,
                title=f"Problem {uuid4().hex[:8]}",
                instructions="Choose.",
                correct_answer_index=0,
                statements=[
                    {
                        "content": f"Test {i}.",
                        "is_correct": True,
                        "translation": "Test.",
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
            await prob_repo.create_problem(problem)

        # Test service
        service = GenerationRequestService(gen_repo, prob_repo)
        (
            result_request,
            result_problems,
        ) = await service.get_generation_request_with_entities(gen_request.id)

        # Should return problems for entity_type=problem
        assert result_request.entity_type == EntityType.PROBLEM
        assert len(result_problems) == 2
