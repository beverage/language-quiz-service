"""
Factory functions for manual service instantiation.

These functions create service and repository instances without FastAPI's dependency injection,
suitable for use in middleware, background tasks, CLI, testing, and other contexts where
FastAPI's DI system is not available.

Key differences from dependencies.py:
- No Depends() parameters
- Manual instantiation of all dependencies
- Can be called from anywhere in "Pure Python World"
- Fresh instances created each time to avoid event loop binding issues

For FastAPI routes, use dependencies.py instead.
"""

from typing import Any

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
# Repository Factory Functions
# =============================================================================


async def create_verb_repository() -> VerbRepository:
    """Create verb repository instance using shared connection."""
    client = await get_supabase_client()
    return VerbRepository(client=client)


async def create_sentence_repository() -> SentenceRepository:
    """Create sentence repository instance using shared connection."""
    client = await get_supabase_client()
    return SentenceRepository(client=client)


async def create_problem_repository() -> ProblemRepository:
    """Create problem repository instance using shared connection."""
    client = await get_supabase_client()
    return ProblemRepository(client=client)


async def create_api_key_repository() -> ApiKeyRepository:
    """Create API key repository instance using shared connection."""
    client = await get_supabase_client()
    return ApiKeyRepository(client=client)


async def create_generation_request_repository() -> GenerationRequestRepository:
    """Create generation request repository instance using shared connection."""
    client = await get_supabase_client()
    return GenerationRequestRepository(client=client)


# =============================================================================
# Service Factory Functions (Fresh instances each call)
# =============================================================================


async def create_verb_service() -> VerbService:
    """Create fresh verb service instance.

    Each call creates a new instance to avoid event loop binding issues.
    """
    repository = await create_verb_repository()
    return VerbService(
        llm_client=get_client(),
        verb_repository=repository,
    )


async def create_sentence_service() -> SentenceService:
    """Create fresh sentence service instance.

    Each call creates a new instance to avoid event loop binding issues.
    """
    verb_service = await create_verb_service()
    sentence_repository = await create_sentence_repository()
    return SentenceService(
        llm_client=get_client(),
        sentence_repository=sentence_repository,
        verb_service=verb_service,
    )


async def create_problem_service() -> ProblemService:
    """Create fresh problem service instance.

    Each call creates a new instance to avoid event loop binding issues.
    """
    problem_repository = await create_problem_repository()
    sentence_service = await create_sentence_service()
    verb_service = await create_verb_service()
    return ProblemService(
        problem_repository=problem_repository,
        sentence_service=sentence_service,
        verb_service=verb_service,
    )


async def create_api_key_service() -> ApiKeyService:
    """Create fresh API key service instance.

    Each call creates a new instance to avoid event loop binding issues.
    This is particularly important for middleware usage where event loops
    may differ between requests.
    """
    repository = await create_api_key_repository()
    return ApiKeyService(api_key_repository=repository)


async def create_generation_request_service() -> GenerationRequestService:
    """Create fresh generation request service instance.

    Each call creates a new instance to avoid event loop binding issues.
    """
    gen_request_repository = await create_generation_request_repository()
    problem_repository = await create_problem_repository()
    return GenerationRequestService(
        generation_request_repository=gen_request_repository,
        problem_repository=problem_repository,
    )


# =============================================================================
# Bundle Functions (Fresh instances for specific use cases)
# =============================================================================


async def create_repositories_bundle() -> dict[str, Any]:
    """Create all repositories using shared connection."""
    client = await get_supabase_client()
    return {
        "verb": VerbRepository(client=client),
        "sentence": SentenceRepository(client=client),
        "problem": ProblemRepository(client=client),
        "api_key": ApiKeyRepository(client=client),
        "generation_request": GenerationRequestRepository(client=client),
    }
