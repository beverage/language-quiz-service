"""
Factory functions for manual service instantiation.

These functions create service and repository instances without FastAPI's dependency injection,
suitable for use in CLI commands, background workers, testing, and other contexts where
FastAPI's DI system is not available.

Key differences from dependencies.py:
- No Depends() parameters
- Manual instantiation of all dependencies
- Can be called from anywhere in "Pure Python World"
- Uses module-level singleton for Supabase client (shared across calls)

For FastAPI routes, use dependencies.py instead (which uses app.state).
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
    """Create verb repository instance using singleton Supabase client."""
    client = await get_supabase_client()
    return VerbRepository(client=client)


async def create_sentence_repository() -> SentenceRepository:
    """Create sentence repository instance using singleton Supabase client."""
    client = await get_supabase_client()
    return SentenceRepository(client=client)


async def create_problem_repository() -> ProblemRepository:
    """Create problem repository instance using singleton Supabase client."""
    client = await get_supabase_client()
    return ProblemRepository(client=client)


async def create_api_key_repository() -> ApiKeyRepository:
    """Create API key repository instance using singleton Supabase client."""
    client = await get_supabase_client()
    return ApiKeyRepository(client=client)


async def create_generation_request_repository() -> GenerationRequestRepository:
    """Create generation request repository instance using singleton Supabase client."""
    client = await get_supabase_client()
    return GenerationRequestRepository(client=client)


# =============================================================================
# Service Factory Functions (Fresh instances each call)
# =============================================================================


async def get_redis_client():
    """Get Redis client for CLI/worker contexts.

    Returns None if Redis is not configured.
    """
    import redis.asyncio as aioredis

    from src.core.config import settings

    if not settings.redis_url:
        return None
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def create_verb_service() -> VerbService:
    """Create fresh verb service instance with cache support.

    Each call creates a new instance to avoid event loop binding issues.
    Includes Redis cache if Redis is configured.
    """
    from src.cache.conjugation_cache import ConjugationCache
    from src.cache.verb_cache import VerbCache

    repository = await create_verb_repository()
    redis_client = await get_redis_client()

    verb_cache = VerbCache(redis_client) if redis_client else None
    conjugation_cache = ConjugationCache(redis_client) if redis_client else None

    return VerbService(
        llm_client=get_client(),
        verb_repository=repository,
        verb_cache=verb_cache,
        conjugation_cache=conjugation_cache,
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


async def create_api_key_service(
    redis_client=None,
) -> ApiKeyService:
    """Create API key service instance for CLI/worker contexts.

    Uses singleton Supabase client. For FastAPI routes, use dependencies.py instead.

    Args:
        redis_client: Optional Redis client for caching. If not provided,
            the service will work without caching (database-only).
    """
    from src.cache.api_key_cache import ApiKeyCache

    repository = await create_api_key_repository()
    api_key_cache = ApiKeyCache(redis_client) if redis_client else None
    return ApiKeyService(api_key_repository=repository, api_key_cache=api_key_cache)


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
    """Create all repositories using singleton Supabase client."""
    client = await get_supabase_client()
    return {
        "verb": VerbRepository(client=client),
        "sentence": SentenceRepository(client=client),
        "problem": ProblemRepository(client=client),
        "api_key": ApiKeyRepository(client=client),
        "generation_request": GenerationRequestRepository(client=client),
    }
