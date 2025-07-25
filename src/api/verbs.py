"""Verb management endpoints."""

import logging
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.models.verbs import (
    VerbDownloadRequest,
    VerbResponse,
    VerbWithConjugationsResponse,
)
from src.core.auth import get_current_api_key
from src.core.exceptions import (
    AppException,
    ContentGenerationError,
    NotFoundError,
    RepositoryError,
    ServiceError,
)
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verbs", tags=["verbs"])


@router.post(
    "/download",
    response_model=VerbResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Download and store a new French verb",
    description="""
    Download a French verb from AI service and store it in the database.

    This endpoint uses AI to generate comprehensive verb information including:
    - **Conjugations**: Complete conjugation tables for all supported tenses
    - **Auxiliary Information**: Whether the verb uses avoir or être
    - **Participle Forms**: Past participle (for compound tenses) and present participle
    - **Classification**: French verb group (1st, 2nd, or 3rd group)
    - **Grammatical Properties**: Irregularity status, direct/indirect object compatibility
    - **Translation**: Target language translation with language code support

    **Input Requirements:**
    - `infinitive`: French verb in infinitive form (e.g., "parler", "être", "se lever")
    - `target_language_code`: ISO 639-3 language code for translation (default: "eng")

    **AI Processing:**
    The endpoint leverages advanced language models to:
    1. Validate the French verb exists and is properly formed
    2. Generate complete conjugation patterns for all tenses
    3. Determine auxiliary verb requirements and reflexivity
    4. Classify the verb according to French grammar rules
    5. Provide accurate translations in the target language

    **Use Cases:**
    - Expanding vocabulary database with new verbs
    - Educational content creation for language learning
    - Automated curriculum development
    - Language analysis and linguistic research

    **Required Permission**: `write` or `admin`
    """,
    responses={
        201: {
            "description": "Verb successfully downloaded and stored",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "infinitive": "parler",
                        "auxiliary": "avoir",
                        "reflexive": False,
                        "target_language_code": "eng",
                        "translation": "to speak",
                        "past_participle": "parlé",
                        "present_participle": "parlant",
                        "classification": "first_group",
                        "is_irregular": False,
                        "can_have_cod": True,
                        "can_have_coi": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "last_used_at": None,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request parameters or verb not found",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_verb": {
                            "summary": "Invalid French verb",
                            "value": {
                                "error": True,
                                "message": "Invalid French verb 'xyz123' - not found in French dictionary",
                                "status_code": 400,
                                "path": "/api/v1/verbs/download",
                            },
                        },
                        "invalid_language": {
                            "summary": "Invalid language code",
                            "value": {
                                "error": True,
                                "message": "Invalid language code 'xyz' - must be ISO 639-3 format",
                                "status_code": 400,
                                "path": "/api/v1/verbs/download",
                            },
                        },
                    }
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Write or admin permission required to download verbs",
                        "status_code": 403,
                        "path": "/api/v1/verbs/download",
                    }
                }
            },
        },
        422: {
            "description": "Request validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Request validation failed",
                        "status_code": 422,
                        "path": "/api/v1/verbs/download",
                        "details": [
                            {
                                "field": "infinitive",
                                "message": "String should have at least 1 character",
                                "type": "string_too_short",
                            }
                        ],
                    }
                }
            },
        },
        500: {
            "description": "AI service error or internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Failed to download verb - AI service temporarily unavailable",
                        "status_code": 500,
                        "path": "/api/v1/verbs/download",
                    }
                }
            },
        },
    },
)
async def download_verb(
    request: VerbDownloadRequest,
    current_key: dict = Depends(get_current_api_key),
) -> VerbResponse:
    """
    Download a verb from LLM and store it.

    Requires 'write' or 'admin' permission.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "write" not in permissions and "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write or admin permission required to download verbs",
        )

    try:
        service = VerbService()
        verb = await service.download_verb(
            requested_verb=request.infinitive,
            target_language_code=request.target_language_code,
        )

        logger.info(
            f"Downloaded verb {request.infinitive} by {current_key.get('name', 'unknown')}"
        )

        # Convert service schema to API response model
        return VerbResponse(**verb.model_dump())

    except ContentGenerationError as e:
        # If the verb already exists, it's a conflict
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        # Otherwise, it's a service unavailable error from the LLM
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        # Pass through with the status code from the exception
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        # Catch-all for other custom app exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the verb.",
        )


@router.get(
    "/random",
    response_model=VerbResponse,
    summary="Get a random French verb",
    description="""
    Retrieve a random French verb from the database.

    This endpoint is useful for:
    - Language learning applications
    - Quiz generation
    - Vocabulary practice
    - Random content exploration

    **Required Permission**: `read`, `write`, or `admin`
    """,
    responses={
        200: {
            "description": "Random verb retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "456e7890-e89b-12d3-a456-426614174111",
                        "infinitive": "manger",
                        "auxiliary": "avoir",
                        "reflexive": False,
                        "target_language_code": "eng",
                        "translation": "to eat",
                        "past_participle": "mangé",
                        "present_participle": "mangeant",
                        "classification": "first_group",
                        "is_irregular": False,
                        "can_have_cod": True,
                        "can_have_coi": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "last_used_at": "2024-01-15T14:22:00Z",
                    }
                }
            },
        },
        404: {
            "description": "No verbs found in database",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "No verbs found",
                        "status_code": 404,
                        "path": "/verbs/random",
                    }
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Read permission required to access verbs",
                        "status_code": 403,
                        "path": "/verbs/random",
                    }
                }
            },
        },
    },
)
async def get_random_verb(
    target_language_code: str = Query(
        "eng", description="Target language code for translation", examples=["eng"]
    ),
    current_key: dict = Depends(get_current_api_key),
) -> VerbResponse:
    """
    Get a random verb.

    Requires 'read' or higher permission.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if (
        "read" not in permissions
        and "write" not in permissions
        and "admin" not in permissions
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required to access verbs",
        )

    try:
        service = VerbService()
        verb = await service.get_random_verb(target_language_code=target_language_code)

        if not verb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No verbs found"
            )

        return VerbResponse(**verb.model_dump())

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/{infinitive}",
    response_model=VerbResponse,
    summary="Get verb by infinitive with optional filters",
    description="""
    Retrieve a specific French verb by its infinitive form.

    **Important: Verb Identification**

    Verbs are uniquely identified by: `(infinitive, auxiliary, reflexive, target_language_code)`
    - Multiple variants of the same infinitive can exist (e.g., "sortir" with avoir vs être)
    - The same French verb can have different representations for different target languages
    - Use auxiliary, reflexive, and target_language_code parameters to specify the exact variant

    **URL Encoding:**
    The infinitive supports URL encoding for verbs with spaces (e.g., reflexive verbs like "se laver").

    **Optional Filters:**
    - `auxiliary`: Filter by auxiliary verb type (avoir/être)
    - `reflexive`: Filter by reflexive status (true/false)
    - `target_language_code`: Filter by target language (part of uniqueness)

    **Examples:**
    - `/verbs/parler` - Returns any "parler" variant (usually avoir, non-reflexive, eng)
    - `/verbs/sortir?auxiliary=avoir` - Returns "sortir" with auxiliary avoir
    - `/verbs/sortir?auxiliary=être` - Returns "sortir" with auxiliary être
    - `/verbs/se%20laver?reflexive=true` - Returns the reflexive verb "se laver"

    **Use Cases:**
    - Vocabulary lookup for language learning applications
    - Grammar rule verification and conjugation reference
    - Content generation for educational materials
    - API integration for translation and language tools

    **Required Permission**: `read` or higher
    """,
    responses={
        200: {
            "description": "Verb found and returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "infinitive": "parler",
                        "auxiliary": "avoir",
                        "reflexive": False,
                        "target_language_code": "eng",
                        "translation": "to speak",
                        "past_participle": "parlé",
                        "present_participle": "parlant",
                        "classification": "first_group",
                        "is_irregular": False,
                        "can_have_cod": True,
                        "can_have_coi": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "last_used_at": "2024-01-15T16:45:00Z",
                    }
                }
            },
        },
        404: {
            "description": "Verb not found with specified criteria",
            "content": {
                "application/json": {
                    "examples": {
                        "verb_not_found": {
                            "summary": "Infinitive not found",
                            "value": {
                                "error": True,
                                "message": "Verb 'xyz' not found",
                                "status_code": 404,
                                "path": "/api/v1/verbs/xyz",
                            },
                        },
                        "variant_not_found": {
                            "summary": "Specific variant not found",
                            "value": {
                                "error": True,
                                "message": "Verb 'parler' with auxiliary 'être' not found",
                                "status_code": 404,
                                "path": "/api/v1/verbs/parler?auxiliary=être",
                            },
                        },
                    }
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Read permission required to access verbs",
                        "status_code": 403,
                        "path": "/api/v1/verbs/parler",
                    }
                }
            },
        },
    },
)
async def get_verb_by_infinitive(
    infinitive: str,
    auxiliary: str | None = Query(
        None, description="Filter by auxiliary verb type", examples=["avoir"]
    ),
    reflexive: bool | None = Query(
        None, description="Filter by reflexive status", examples=[False]
    ),
    target_language_code: str = Query(
        "eng", description="Target language code for translation", examples=["eng"]
    ),
    current_key: dict = Depends(get_current_api_key),
) -> VerbResponse:
    """
    Get a verb by infinitive (supports URL encoding for spaces).

    Requires 'read' or higher permission.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if (
        "read" not in permissions
        and "write" not in permissions
        and "admin" not in permissions
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required to access verbs",
        )

    try:
        # URL decode the infinitive to handle spaces
        decoded_infinitive = unquote(infinitive)

        service = VerbService()
        verb = await service.get_verb_by_infinitive(
            infinitive=decoded_infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )

        if not verb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verb '{decoded_infinitive}' not found",
            )

        return VerbResponse(**verb.model_dump())

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verb",
        )


@router.get(
    "/{infinitive}/conjugations",
    response_model=VerbWithConjugationsResponse,
    summary="Get verb conjugations with complete tense information",
    description="""
    Retrieve comprehensive conjugation information for a French verb across all supported tenses.

    **Important: Verb Identification**

    Verbs are uniquely identified by: `(infinitive, auxiliary, reflexive, target_language_code)`
    - Multiple variants can exist for the same infinitive (e.g., "sortir" + avoir vs "sortir" + être)
    - The same French verb can have different representations for different target languages
    - Specify auxiliary, reflexive, and target_language_code parameters to get the exact variant

    **Conjugation Coverage:**
    Returns conjugations for all available tenses including:
    - **Indicative**: présent, passé composé, imparfait, futur simple, conditionnel
    - **Subjunctive**: subjonctif présent
    - **Imperative**: impératif présent

    **Response Format:**
    - Complete verb metadata (participles, classification, grammatical properties)
    - Array of conjugation objects, each containing all six persons for a specific tense
    - Tense-specific conjugation patterns with person markers (je/tu/il/nous/vous/ils)

    **URL Encoding:**
    Supports URL encoding for verbs with spaces (e.g., "se%20laver" for reflexive verbs).

    **Filtering Options:**
    - `auxiliary`: Specify auxiliary verb (avoir/être) to get exact variant
    - `reflexive`: Specify reflexive status (true/false) for precise identification
    - `target_language_code`: Specify target language (part of uniqueness)

    **Examples:**
    - `/verbs/parler/conjugations` - All conjugations for "parler" (avoir, non-reflexive, eng)
    - `/verbs/sortir/conjugations?auxiliary=avoir` - "sortir" with auxiliary avoir
    - `/verbs/sortir/conjugations?auxiliary=être` - "sortir" with auxiliary être
    - `/verbs/se%20laver/conjugations?reflexive=true` - Reflexive "se laver"

    **Use Cases:**
    - Language learning applications requiring complete conjugation tables
    - Grammar checking tools and educational content generation
    - Translation services needing accurate French verb forms
    - Linguistic analysis and computational grammar applications

    **Required Permission**: `read` or higher
    """,
    responses={
        200: {
            "description": "Verb conjugations retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "789e1234-e89b-12d3-a456-426614174222",
                        "infinitive": "parler",
                        "auxiliary": "avoir",
                        "reflexive": False,
                        "target_language_code": "eng",
                        "translation": "to speak",
                        "past_participle": "parlé",
                        "present_participle": "parlant",
                        "classification": "first_group",
                        "is_irregular": False,
                        "can_have_cod": True,
                        "can_have_coi": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "last_used_at": "2024-01-15T16:45:00Z",
                        "conjugations": [
                            {
                                "tense": "present",
                                "first_person_singular": "parle",
                                "second_person_singular": "parles",
                                "third_person_singular": "parle",
                                "first_person_plural": "parlons",
                                "second_person_plural": "parlez",
                                "third_person_plural": "parlent",
                            },
                            {
                                "tense": "passe_compose",
                                "first_person_singular": "ai parlé",
                                "second_person_singular": "as parlé",
                                "third_person_singular": "a parlé",
                                "first_person_plural": "avons parlé",
                                "second_person_plural": "avez parlé",
                                "third_person_plural": "ont parlé",
                            },
                        ],
                    }
                }
            },
        },
        404: {
            "description": "Verb not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Verb 'nonexistent' not found",
                        "status_code": 404,
                        "path": "/verbs/nonexistent/conjugations",
                    }
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Read permission required to access verbs",
                        "status_code": 403,
                        "path": "/verbs/parler/conjugations",
                    }
                }
            },
        },
    },
)
async def get_verb_conjugations(
    infinitive: str,
    auxiliary: str | None = Query(
        None, description="Filter by auxiliary verb type", examples=["avoir"]
    ),
    reflexive: bool = Query(
        False, description="Filter by reflexive status", examples=[False]
    ),
    target_language_code: str = Query(
        "eng", description="Target language code for translation", examples=["eng"]
    ),
    current_key: dict = Depends(get_current_api_key),
) -> VerbWithConjugationsResponse:
    """
    Get verb conjugations (supports URL encoding for spaces).

    Requires 'read' or higher permission.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if (
        "read" not in permissions
        and "write" not in permissions
        and "admin" not in permissions
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required to access verbs",
        )

    try:
        # URL decode the infinitive to handle spaces
        decoded_infinitive = unquote(infinitive)

        service = VerbService()
        verb_with_conjugations = await service.get_verb_with_conjugations(
            infinitive=decoded_infinitive,
            auxiliary=auxiliary,
            reflexive=reflexive,
            target_language_code=target_language_code,
        )

        if not verb_with_conjugations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verb '{decoded_infinitive}' not found",
            )

        return VerbWithConjugationsResponse(**verb_with_conjugations.model_dump())

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verb conjugations",
        )
