"""Problem management endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.models.problems import (
    ProblemRandomRequest,
    ProblemResponse,
)
from src.core.auth import get_current_api_key
from src.core.exceptions import ContentGenerationError, LanguageResourceNotFoundError
from src.services.problem_service import ProblemService

logger = logging.getLogger(__name__)

# Get limiter instance
limiter = Limiter(key_func=get_remote_address)

API_PREFIX = "/problems"
router = APIRouter(prefix=API_PREFIX, tags=["problems"])


async def get_problem_service() -> ProblemService:
    """Dependency to get ProblemService instance."""
    return ProblemService()


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
        problem = await service.get_random_problem()

        if problem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No problems available",
            )

        logger.info(
            f"Retrieved random problem {problem.id} for API key {current_key.get('name', 'unknown')}"
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
    response_model=ProblemResponse,
    summary="Generate random grammar problem",
    description="""
    Generate a random grammar problem using AI services.

    This endpoint creates fresh, AI-generated problems for language learning:
    - **Grammar Focus**: Targets specific grammatical concepts
    - **Verb Conjugation**: Tests proper verb forms and tenses
    - **Object Usage**: Validates direct/indirect object placement
    - **Negation Patterns**: Challenges with negative constructions
    - **Multiple Choice**: Provides correct answer with plausible distractors

    **Request Body** (all optional):
    ```json
    {
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

    **Query Parameters**:
    - `include_metadata`: Include source_statement_ids and metadata in response (default: false)

    **Required Permission**: `read`, `write`, or `admin`
    """,
    responses={
        200: {
            "description": "Random problem generated successfully",
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
        422: {
            "description": "Request cannot be processed",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "No verbs available for problem generation",
                        "status_code": 422,
                        "path": "/api/v1/problems/generate",
                    }
                }
            },
        },
        503: {
            "description": "Content generation service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Content generation failed",
                        "status_code": 503,
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
    include_metadata: bool = False,
    current_key: dict = Depends(get_current_api_key),
    service: ProblemService = Depends(get_problem_service),
    problem_request: ProblemRandomRequest | None = Body(None),
) -> ProblemResponse:
    """
    Generate a random grammar problem.

    Creates a new problem using AI services with the specified constraints.
    If no request body is provided, generates a completely random problem.
    """
    try:
        # Use defaults if no request body provided
        if problem_request is None:
            problem_request = ProblemRandomRequest()

        # Extract parameters
        constraints = problem_request.constraints
        statement_count = problem_request.statement_count

        problem = await service.create_random_grammar_problem(
            constraints=constraints,
            statement_count=statement_count,
            additional_tags=problem_request.topic_tags,
        )

        logger.info(
            f"Generated random problem {problem.id} for API key {current_key.get('name', 'unknown')}"
        )

        return ProblemResponse.from_problem(problem, include_metadata=include_metadata)

    except LanguageResourceNotFoundError as e:
        logger.warning(
            f"Resource not found for random problem generation: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ValueError as e:
        # Handle business rule violations like "No verbs available"
        if "no verbs available" in str(e).lower():
            logger.warning(
                f"No verbs available for problem generation: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )
        else:
            logger.error(
                f"Validation error generating random problem: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except ContentGenerationError as e:
        logger.error(
            f"Content generation failed for random problem: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating random problem: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate random problem",
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
