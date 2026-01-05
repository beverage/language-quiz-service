"""
Dependencies for FastAPI routes.

This module provides FastAPI-style dependency injection using Depends().
Use these functions in API route handlers to get properly wired services.

For non-FastAPI contexts (CLI, workers, tests), use factories.py instead.
"""

from fastapi import Depends

from src.clients import get_client
from src.clients.supabase import get_supabase_client
from src.repositories.api_keys_repository import ApiKeyRepository
from src.repositories.generation_requests_repository import GenerationRequestRepository
from src.repositories.problem_repository import ProblemRepository
from src.repositories.sentence_repository import SentenceRepository
from src.repositories.verb_repository import VerbRepository
from src.services.api_key_service import ApiKeyService
from src.services.generation_request_service import GenerationRequestService
from src.services.problem_service import ProblemService
from src.services.sentence_service import SentenceService
from src.services.verb_service import VerbService

# =============================================================================
# Repository Dependencies
# =============================================================================


async def get_verb_repository() -> VerbRepository:
    """Get verb repository with async client."""
    client = await get_supabase_client()
    return VerbRepository(client=client)


async def get_sentence_repository() -> SentenceRepository:
    """Get sentence repository with async client."""
    client = await get_supabase_client()
    return SentenceRepository(client=client)


async def get_problem_repository() -> ProblemRepository:
    """Get problem repository with async client."""
    client = await get_supabase_client()
    return ProblemRepository(client=client)


async def get_api_key_repository() -> ApiKeyRepository:
    """Get API key repository with async client."""
    client = await get_supabase_client()
    return ApiKeyRepository(client=client)


async def get_generation_request_repository() -> GenerationRequestRepository:
    """Get generation request repository with async client."""
    client = await get_supabase_client()
    return GenerationRequestRepository(client=client)


# =============================================================================
# Service Dependencies
# =============================================================================


async def get_verb_service(
    repository: VerbRepository = Depends(get_verb_repository),
) -> VerbService:
    """Get verb service with dependencies."""
    return VerbService(llm_client=get_client(), verb_repository=repository)


async def get_sentence_service(
    sentence_repository: SentenceRepository = Depends(get_sentence_repository),
    verb_service: VerbService = Depends(get_verb_service),
) -> SentenceService:
    """Get sentence service with dependencies."""
    return SentenceService(
        llm_client=get_client(),
        sentence_repository=sentence_repository,
        verb_service=verb_service,
    )


async def get_problem_service(
    problem_repository: ProblemRepository = Depends(get_problem_repository),
    sentence_service: SentenceService = Depends(get_sentence_service),
    verb_service: VerbService = Depends(get_verb_service),
) -> ProblemService:
    """Get problem service with dependencies."""
    return ProblemService(
        problem_repository=problem_repository,
        sentence_service=sentence_service,
        verb_service=verb_service,
    )


async def get_api_key_service(
    repository: ApiKeyRepository = Depends(get_api_key_repository),
) -> ApiKeyService:
    """Get API key service with dependencies."""
    return ApiKeyService(api_key_repository=repository)


async def get_generation_request_service(
    gen_request_repository: GenerationRequestRepository = Depends(
        get_generation_request_repository
    ),
    problem_repository: ProblemRepository = Depends(get_problem_repository),
) -> GenerationRequestService:
    """Get generation request service with dependencies."""
    return GenerationRequestService(
        generation_request_repository=gen_request_repository,
        problem_repository=problem_repository,
    )
