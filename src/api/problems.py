"""Problem management endpoints."""

import logging
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.models.problems import (
    ProblemGenerationEnqueuedResponse,
    ProblemRandomRequest,
    ProblemResponse,
)
from src.core.auth import get_current_api_key
from src.services.problem_service import ProblemService
from src.services.queue_service import QueueService

logger = logging.getLogger(__name__)

# Get limiter instance
limiter = Limiter(key_func=get_remote_address)

API_PREFIX = "/problems"
router = APIRouter(prefix=API_PREFIX, tags=["Problems"])


async def get_problem_service() -> ProblemService:
    """Dependency to get ProblemService instance."""
    return ProblemService()


async def get_queue_service() -> AsyncGenerator[QueueService, None]:
    """
    Dependency to get QueueService instance with proper cleanup.

    Yields the service and ensures the Kafka producer is closed after the request.
    This prevents "Unclosed AIOKafkaProducer" warnings.
    """
    service = QueueService()
    try:
        yield service
    finally:
        # Clean up Kafka producer connection
        await service.close()


@router.get(
    "/random",
    response_model=ProblemResponse,
    summary="Get random problem from database",
    description="""
    Retrieve a random problem from the database.

    This endpoint fetches an existing problem from the database, providing:
    - **Fast Response**: No AI generation delay
    - **Consistent Problems**: Previously generated and stored problems
    - **Multiple Choice**: Complete problem with all statements and correct answer

    Future enhancements will include filtering by topic, difficulty, and other criteria.

    **Query Parameters**:
    - `include_metadata`: Include source_statement_ids and metadata in response (default: false)

    **Required Permission**: `read`, `write`, or `admin`
    """,
    responses={
        200: {
            "description": "Random problem retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "problem_type": "grammar",
                        "title": "Grammar: Parler",
                        "instructions": "Choose the correctly formed French sentence.",
                        "statements": [
                            {
                                "content": "Je parle français.",
                                "is_correct": True,
                                "translation": "I speak French.",
                            },
                            {
                                "content": "Je parles français.",
                                "is_correct": False,
                                "explanation": "Wrong conjugation - first person singular uses 'parle', not 'parles'",
                            },
                        ],
                        "correct_answer_index": 0,
                        "target_language_code": "eng",
                        "topic_tags": ["grammar", "basic_conjugation"],
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-15T10:30:00Z",
                    }
                }
            },
        },
        404: {
            "description": "No problems available in database",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "No problems available",
                        "status_code": 404,
                        "path": "/api/v1/problems/random",
                    }
                }
            },
        },
    },
)
@limiter.limit("100/minute")
async def get_random_problem(
    request: Request,
    include_metadata: bool = False,
    current_key: dict = Depends(get_current_api_key),
    service: ProblemService = Depends(get_problem_service),
) -> ProblemResponse:
    """
    Get a random problem from the database.

    Fetches a random existing problem without generating new content.
    """
    try:
        # Get least recently served problem
        problem = await service.get_least_recently_served_problem()

        if problem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No problems available",
            )

        logger.info(
            f"Retrieved LRU problem {problem.id} for API key {current_key.get('name', 'unknown')}"
        )

        return ProblemResponse.from_problem(problem, include_metadata=include_metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting random problem: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve random problem",
        )


@router.post(
    "/generate",
    response_model=ProblemGenerationEnqueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue problem generation requests",
    description="""
    Enqueue problem generation requests for async processing.

    This endpoint enqueues problem generation requests to a background worker queue.
    Problems are generated asynchronously and become available via GET /problems/random.

    **Benefits**:
    - **Fast Response**: Returns immediately (202 Accepted)
    - **Bulk Generation**: Generate multiple problems with count parameter
    - **Quality**: Worker can retry and validate problems without blocking API
    - **Scalability**: Decouples API latency from LLM processing time

    **Request Body** (all optional):
    ```json
    {
      "count": 10,
      "constraints": {
        "grammatical_focus": ["direct_objects", "pronoun_placement"],
        "verb_infinitives": ["parler", "manger", "finir"],
        "tenses_used": ["present", "passe_compose"],
        "includes_negation": true,
        "includes_cod": true,
        "includes_coi": false,
        "difficulty_level": "intermediate"
      },
      "statement_count": 4,
      "target_language_code": "eng"
    }
    ```

    **Required Permission**: `read`, `write`, or `admin`
    """,
    responses={
        202: {
            "description": "Generation requests enqueued successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Enqueued 10 problem generation requests",
                        "count": 10,
                    }
                }
            },
        },
        500: {
            "description": "Failed to enqueue requests",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Failed to enqueue problem generation",
                        "status_code": 500,
                        "path": "/api/v1/problems/generate",
                    }
                }
            },
        },
    },
)
@limiter.limit("100/minute")
async def generate_random_problem(
    request: Request,
    current_key: dict = Depends(get_current_api_key),
    queue_service: QueueService = Depends(get_queue_service),
    problem_request: ProblemRandomRequest | None = Body(None),
) -> ProblemGenerationEnqueuedResponse:
    """
    Enqueue problem generation requests for async processing.

    Publishes generation requests to Kafka for background worker processing.
    Returns immediately with 202 Accepted status.
    """
    try:
        # Use defaults if no request body provided
        if problem_request is None:
            problem_request = ProblemRandomRequest()

        # Extract parameters
        constraints = problem_request.constraints
        statement_count = problem_request.statement_count
        topic_tags = problem_request.topic_tags
        count = problem_request.count

        # Enqueue generation requests
        (
            enqueued_count,
            request_id,
        ) = await queue_service.publish_problem_generation_request(
            constraints=constraints,
            statement_count=statement_count,
            topic_tags=topic_tags,
            count=count,
        )

        logger.info(
            f"Enqueued {enqueued_count} problem generation message(s) "
            f"for request {request_id} "
            f"(API key: {current_key.get('name', 'unknown')})"
        )

        return ProblemGenerationEnqueuedResponse(
            message=f"Enqueued {count} problem generation request{'s' if count != 1 else ''}",
            count=count,
            request_id=request_id,
        )

    except Exception as e:
        logger.error(
            f"Unexpected error enqueuing problem generation: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enqueue problem generation",
        )


@router.get(
    "/{problem_id}",
    response_model=ProblemResponse,
    summary="Get specific problem",
    description="""
    Retrieve a specific problem by its unique identifier.

    Returns complete problem information including:
    - All statements with correctness indicators
    - Translations and explanations where available
    - Metadata and categorization tags
    - Creation and modification timestamps

    **Query Parameters**:
    - `include_metadata`: Include source_statement_ids and metadata in response (default: false)

    **Required Permission**: `read`, `write`, or `admin`
    """,
)
async def get_problem(
    problem_id: UUID,
    request: Request,
    include_metadata: bool = False,
    current_key: dict = Depends(get_current_api_key),
    service: ProblemService = Depends(get_problem_service),
) -> ProblemResponse:
    """Get a problem by ID."""
    try:
        problem = await service.get_problem_by_id(problem_id)

        if problem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem not found",
            )

        return ProblemResponse.from_problem(problem, include_metadata=include_metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving problem {problem_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve problem",
        )
