"""
Dependencies for FastAPI routes.

This module provides FastAPI-style dependency injection using Depends().
Use these functions in API route handlers to get properly wired services.

For non-FastAPI contexts (CLI, workers, tests), use factories.py instead.
"""

import redis.asyncio as aioredis
from fastapi import Depends, Request
from supabase import AsyncClient

from src.cache.api_key_cache import ApiKeyCache
from src.cache.conjugation_cache import ConjugationCache
from src.cache.verb_cache import VerbCache
from src.clients import get_client
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
# Supabase and Redis Client Dependencies
# =============================================================================


def get_supabase(request: Request) -> AsyncClient:
    """Get Supabase client from app state (created once at startup)."""
    return request.app.state.supabase


def get_redis(request: Request) -> aioredis.Redis | None:
    """Get Redis client from app state. Returns None if Redis not available."""
    return getattr(request.app.state, "redis", None)


def get_verb_cache(
    redis: aioredis.Redis | None = Depends(get_redis),
) -> VerbCache | None:
    """Get VerbCache instance with Redis client. Returns None if Redis unavailable."""
    if redis is None:
        return None
    return VerbCache(redis)


def get_conjugation_cache(
    redis: aioredis.Redis | None = Depends(get_redis),
) -> ConjugationCache | None:
    """Get ConjugationCache instance with Redis client. Returns None if Redis unavailable."""
    if redis is None:
        return None
    return ConjugationCache(redis)


def get_api_key_cache(
    redis: aioredis.Redis | None = Depends(get_redis),
) -> ApiKeyCache | None:
    """Get ApiKeyCache instance with Redis client. Returns None if Redis unavailable."""
    if redis is None:
        return None
    return ApiKeyCache(redis)


# =============================================================================
# Repository Dependencies
# =============================================================================


def get_verb_repository(
    supabase: AsyncClient = Depends(get_supabase),
) -> VerbRepository:
    """Get verb repository using shared Supabase client from app.state."""
    return VerbRepository(client=supabase)


def get_sentence_repository(
    supabase: AsyncClient = Depends(get_supabase),
) -> SentenceRepository:
    """Get sentence repository using shared Supabase client from app.state."""
    return SentenceRepository(client=supabase)


def get_problem_repository(
    supabase: AsyncClient = Depends(get_supabase),
) -> ProblemRepository:
    """Get problem repository using shared Supabase client from app.state."""
    return ProblemRepository(client=supabase)


def get_api_key_repository(
    supabase: AsyncClient = Depends(get_supabase),
) -> ApiKeyRepository:
    """Get API key repository using shared Supabase client from app.state."""
    return ApiKeyRepository(client=supabase)


def get_generation_request_repository(
    supabase: AsyncClient = Depends(get_supabase),
) -> GenerationRequestRepository:
    """Get generation request repository using shared Supabase client from app.state."""
    return GenerationRequestRepository(client=supabase)


# =============================================================================
# Service Dependencies
# =============================================================================


def get_verb_service(
    repository: VerbRepository = Depends(get_verb_repository),
    verb_cache: VerbCache | None = Depends(get_verb_cache),
    conjugation_cache: ConjugationCache | None = Depends(get_conjugation_cache),
) -> VerbService:
    """Get verb service with dependencies."""
    return VerbService(
        llm_client=get_client(),
        verb_repository=repository,
        verb_cache=verb_cache,
        conjugation_cache=conjugation_cache,
    )


def get_sentence_service(
    sentence_repository: SentenceRepository = Depends(get_sentence_repository),
    verb_service: VerbService = Depends(get_verb_service),
) -> SentenceService:
    """Get sentence service with dependencies."""
    return SentenceService(
        llm_client=get_client(),
        sentence_repository=sentence_repository,
        verb_service=verb_service,
    )


def get_problem_service(
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


def get_api_key_service(
    repository: ApiKeyRepository = Depends(get_api_key_repository),
    api_key_cache: ApiKeyCache | None = Depends(get_api_key_cache),
) -> ApiKeyService:
    """Get API key service with dependencies."""
    return ApiKeyService(api_key_repository=repository, api_key_cache=api_key_cache)


def get_generation_request_service(
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
