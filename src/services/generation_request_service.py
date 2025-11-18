"""Generation request service for business logic."""

import logging
from uuid import UUID

from src.core.exceptions import NotFoundError
from src.repositories.generation_requests_repository import (
    GenerationRequestRepository,
)
from src.repositories.problem_repository import ProblemRepository
from src.schemas.generation_requests import GenerationRequest
from src.schemas.problems import Problem

logger = logging.getLogger(__name__)


class GenerationRequestService:
    """Service for generation request business logic and orchestration."""

    def __init__(
        self,
        generation_request_repository: GenerationRequestRepository | None = None,
        problem_repository: ProblemRepository | None = None,
    ):
        """Initialize the generation request service with injectable dependencies."""
        self.generation_request_repository = generation_request_repository
        self.problem_repository = problem_repository

    async def _get_generation_request_repository(
        self,
    ) -> GenerationRequestRepository:
        """Asynchronously get the generation request repository, creating it if it doesn't exist."""
        if self.generation_request_repository is None:
            self.generation_request_repository = (
                await GenerationRequestRepository.create()
            )
        return self.generation_request_repository

    async def _get_problem_repository(self) -> ProblemRepository:
        """Asynchronously get the problem repository, creating it if it doesn't exist."""
        if self.problem_repository is None:
            self.problem_repository = await ProblemRepository.create()
        return self.problem_repository

    async def get_generation_request_with_entities(
        self, request_id: UUID
    ) -> tuple[GenerationRequest, list[Problem]]:
        """
        Get a generation request by ID along with all generated entities.

        Args:
            request_id: UUID of the generation request

        Returns:
            Tuple of (GenerationRequest, list of Problems)

        Raises:
            NotFoundError: If generation request not found
        """
        gen_request_repo = await self._get_generation_request_repository()
        await self._get_problem_repository()

        # Get the generation request
        generation_request = await gen_request_repo.get_generation_request(request_id)
        if not generation_request:
            raise NotFoundError(f"Generation request with ID {request_id} not found")

        # Get associated problems (only for problem entity type)
        problems = []
        if generation_request.entity_type == "problem":
            problem_data_list = await gen_request_repo.get_problems_by_request_id(
                request_id
            )

            # Convert raw data to Problem models
            for problem_data in problem_data_list:
                # Use the repository's data preparation if available
                # Otherwise validate directly
                try:
                    problem = Problem.model_validate(problem_data)
                    problems.append(problem)
                except Exception as e:
                    logger.error(
                        f"Failed to validate problem data from request {request_id}: {e}"
                    )
                    # Continue processing other problems

        logger.info(
            f"Retrieved generation request {request_id} with {len(problems)} problem(s)"
        )

        return generation_request, problems
