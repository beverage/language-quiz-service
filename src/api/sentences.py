"""
Sentence management endpoints.

Provides read-only access to sentence data with filtering capabilities.
Sentence creation and updates are handled through internal services only.

Available Endpoints:
- GET /random - Retrieve a random sentence
- GET /{sentence_id} - Get specific sentence by ID
- GET / - List sentences with optional filters
- DELETE /{sentence_id} - Remove a sentence from the database

Note: Creation and update endpoints have been removed as sentence
generation requires complex grammatical validation best handled by AI services.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

# Add authentication dependency
# Authentication enforced by middleware
from src.api.models.sentences import SentenceResponse
from src.core.auth import get_current_api_key
from src.core.dependencies import get_sentence_service
from src.core.exceptions import (
    AppException,
    ContentGenerationError,
    NotFoundError,
    RepositoryError,
    ServiceError,
)
from src.services.sentence_service import SentenceService

API_PREFIX = "/sentences"
router = APIRouter(prefix=API_PREFIX, tags=["Sentences"])


@router.get(
    "/random",
    response_model=SentenceResponse,
    summary="Get random sentence",
    description="""
    Retrieve a random sentence from the database with optional filtering.

    This endpoint is useful for:
    - Language learning applications requiring random content
    - Quiz generation with diverse sentence structures
    - Vocabulary practice with varied contexts
    - Content discovery and exploration

    Filtering Options:
    - Filter by correctness to get only valid sentences for learning
    - Filter by verb to focus on specific vocabulary

    Required Permission: read, write, or admin
    """,
    responses={
        200: {
            "description": "Random sentence retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "789e1234-e89b-12d3-a456-426614174333",
                        "target_language_code": "eng",
                        "content": "Je parle français couramment.",
                        "translation": "I speak French fluently.",
                        "verb_id": "123e4567-e89b-12d3-a456-426614174000",
                        "pronoun": "first_person",
                        "tense": "present",
                        "direct_object": "masculine",
                        "indirect_object": "none",
                        "negation": "none",
                        "is_correct": True,
                        "explanation": "Present tense with adverb of manner",
                        "source": "AI_GENERATED",
                        "created_at": "2024-01-15T11:30:00Z",
                        "updated_at": "2024-01-15T11:30:00Z",
                    }
                }
            },
        },
        404: {
            "description": "No sentences found matching criteria",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "No sentences found matching criteria",
                        "status_code": 404,
                        "path": "/api/v1/sentences/random",
                    }
                }
            },
        },
    },
)
async def get_random_sentence(
    is_correct: bool | None = Query(
        None,
        description="Filter by correctness (true for grammatically correct sentences only)",
    ),
    verb_id: UUID | None = Query(
        None,
        description="Filter by specific verb UUID to get sentences using that verb",
    ),
    service: SentenceService = Depends(get_sentence_service),
) -> SentenceResponse:
    """
    Get a random sentence from the database.

    Optionally filter by correctness and/or verb ID.
    """
    try:
        sentence = await service.get_random_sentence(
            is_correct=is_correct,
            verb_id=str(verb_id) if verb_id is not None else None,
        )
        if not sentence:
            raise NotFoundError("No sentences found matching criteria")
        return SentenceResponse(**sentence.model_dump())
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError, ContentGenerationError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{sentence_id}",
    response_model=SentenceResponse,
    summary="Get sentence by ID",
    description="""
    Retrieve a specific sentence using its unique identifier.

    Use Cases:
    - Display detailed sentence information in learning interfaces
    - Retrieve sentences for analysis or modification workflows
    - Access specific content referenced by ID from other systems

    Required Permission: read, write, or admin
    """,
    responses={
        200: {
            "description": "Sentence found and retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "789e1234-e89b-12d3-a456-426614174333",
                        "target_language_code": "eng",
                        "content": "Nous avons parlé de littérature.",
                        "translation": "We talked about literature.",
                        "verb_id": "123e4567-e89b-12d3-a456-426614174000",
                        "pronoun": "first_person_plural",
                        "tense": "passe_compose",
                        "direct_object": "none",
                        "indirect_object": "thing",
                        "negation": "none",
                        "is_correct": True,
                        "explanation": "Passé composé with indirect object 'de quelque chose'",
                        "source": "AI_GENERATED",
                        "created_at": "2024-01-15T11:30:00Z",
                        "updated_at": "2024-01-15T11:30:00Z",
                    }
                }
            },
        },
        404: {
            "description": "Sentence not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Sentence not found",
                        "status_code": 404,
                        "path": "/api/v1/sentences/789e1234-e89b-12d3-a456-426614174333",
                    }
                }
            },
        },
    },
)
async def get_sentence(
    sentence_id: UUID,
    service: SentenceService = Depends(get_sentence_service),
) -> SentenceResponse:
    """Get a specific sentence by its ID."""
    try:
        sentence = await service.get_sentence(sentence_id)
        if not sentence:
            raise NotFoundError("Sentence not found")
        return SentenceResponse(**sentence.model_dump())
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/",
    response_model=list[SentenceResponse],
    summary="List sentences with filters",
    description="""
    Retrieve a filtered list of sentences from the database.

    Advanced Filtering:
    Combine multiple filters to create targeted queries:
    - Verb-specific sentences for focused vocabulary practice
    - Tense-based filtering for grammar lessons
    - Correctness filtering for quality control
    - Language-specific content for multi-language support

    Pagination:
    Use the limit parameter to control result size (1-100 sentences).

    Use Cases:
    - Build vocabulary exercises focused on specific verbs
    - Create grammar lessons targeting particular tenses
    - Generate quiz content with known difficulty levels
    - Analyze sentence patterns and structures

    Required Permission: read, write, or admin
    """,
    responses={
        200: {
            "description": "List of sentences matching the filters",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "789e1234-e89b-12d3-a456-426614174333",
                            "target_language_code": "eng",
                            "content": "Je parle français.",
                            "translation": "I speak French.",
                            "verb_id": "123e4567-e89b-12d3-a456-426614174000",
                            "pronoun": "first_person",
                            "tense": "present",
                            "direct_object": "masculine",
                            "indirect_object": "none",
                            "negation": "none",
                            "is_correct": True,
                            "explanation": "Simple present tense with direct object",
                            "source": "AI_GENERATED",
                            "created_at": "2024-01-15T11:30:00Z",
                            "updated_at": "2024-01-15T11:30:00Z",
                        },
                        {
                            "id": "789e1234-e89b-12d3-a456-426614174334",
                            "target_language_code": "eng",
                            "content": "Tu parles très bien.",
                            "translation": "You speak very well.",
                            "verb_id": "123e4567-e89b-12d3-a456-426614174000",
                            "pronoun": "second_person",
                            "tense": "present",
                            "direct_object": "none",
                            "indirect_object": "none",
                            "negation": "none",
                            "is_correct": True,
                            "explanation": "Present tense with adverb of manner",
                            "source": "AI_GENERATED",
                            "created_at": "2024-01-15T11:31:00Z",
                            "updated_at": "2024-01-15T11:31:00Z",
                        },
                    ]
                }
            },
        }
    },
)
async def list_sentences(
    verb_id: UUID | None = Query(
        None, description="Filter sentences by specific verb UUID"
    ),
    is_correct: bool | None = Query(
        None, description="Filter by grammatical correctness (true/false)"
    ),
    tense: str | None = Query(
        None,
        description="Filter by verb tense (present, passe_compose, imparfait, etc.)",
    ),
    pronoun: str | None = Query(
        None,
        description="Filter by subject pronoun (first_person, second_person, etc.)",
    ),
    target_language_code: str | None = Query(
        None, description="Filter by target language code for translations"
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of results to return (1-100)"
    ),
    service: SentenceService = Depends(get_sentence_service),
) -> list[SentenceResponse]:
    """
    List sentences with optional filters.

    Supports filtering by verb, correctness, grammatical features, and language.
    """
    try:
        sentences = await service.get_sentences_by_verb(
            verb_id=str(verb_id) if verb_id else None,
            limit=limit,
        )
        return [SentenceResponse(**s.model_dump()) for s in sentences]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{sentence_id}",
    summary="Delete sentence",
    description="""
    Remove a sentence from the database.

    Use Cases:
    - Content moderation and quality control
    - Removing outdated or incorrect sentences
    - Database maintenance and cleanup

    Required Permission: write or admin

    Note: This operation is irreversible. Deleted sentences cannot be recovered.
    """,
    responses={
        200: {
            "description": "Sentence deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Sentence deleted successfully"}
                }
            },
        },
        404: {
            "description": "Sentence not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Sentence not found",
                        "status_code": 404,
                        "path": "/api/v1/sentences/789e1234-e89b-12d3-a456-426614174333",
                    }
                }
            },
        },
    },
)
async def delete_sentence(
    sentence_id: UUID,
    service: SentenceService = Depends(get_sentence_service),
    current_key: dict = Depends(get_current_api_key),
) -> dict:
    """Delete a sentence from the database."""
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "write" not in permissions and "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write or admin permission required to delete sentences",
        )

    try:
        await service.delete_sentence(sentence_id)
        return {"message": "Sentence deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
