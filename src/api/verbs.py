"""Verb management endpoints."""

import logging
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.auth import get_current_api_key
from src.schemas.verbs import Verb, VerbWithConjugations
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verbs", tags=["verbs"])


@router.post(
    "/download",
    response_model=Verb,
    summary="Download and store a new French verb",
    description="""
    Download a French verb from AI service and store it in the database.

    This endpoint uses AI to generate comprehensive verb information including:
    - Conjugations for all tenses
    - Auxiliary verb information
    - Participle forms
    - Classification and irregularity status
    - Translation to target language

    **Required Permission**: `write` or `admin`
    """,
    responses={
        200: {
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
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Invalid verb or language code",
                        "status_code": 400,
                        "path": "/verbs/download",
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
                        "path": "/verbs/download",
                    }
                }
            },
        },
    },
)
async def download_verb(
    infinitive: str = Query(
        ..., description="French verb in infinitive form", examples=["parler"]
    ),
    target_language_code: str = Query(
        "eng", description="Target language code (ISO 639-3)", examples=["eng"]
    ),
    current_key: dict = Depends(get_current_api_key),
) -> Verb:
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
            requested_verb=infinitive, target_language_code=target_language_code
        )

        logger.info(
            f"Downloaded verb {infinitive} by {current_key.get('name', 'unknown')}"
        )
        return verb

    except ValueError as e:
        logger.warning(f"Invalid verb download request: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading verb {infinitive}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download verb",
        )


@router.get(
    "/random",
    response_model=Verb,
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
) -> Verb:
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

        return verb

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random verb: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get random verb",
        )


@router.get(
    "/{infinitive}",
    response_model=Verb,
    summary="Get specific French verb by infinitive",
    description="""
    Retrieve a specific French verb by its infinitive form.

    **URL Encoding**: Supports URL encoding for verbs with spaces (e.g., "se%20lever" for "se lever")

    **Filtering Options**:
    - `auxiliary`: Filter by auxiliary verb type (avoir/être)
    - `reflexive`: Filter by reflexive status (true/false)
    - `target_language_code`: Specify translation language

    **Required Permission**: `read`, `write`, or `admin`
    """,
    responses={
        200: {
            "description": "Verb found and retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "789e1234-e89b-12d3-a456-426614174222",
                        "infinitive": "être",
                        "auxiliary": "être",
                        "reflexive": False,
                        "target_language_code": "eng",
                        "translation": "to be",
                        "past_participle": "été",
                        "present_participle": "étant",
                        "classification": "third_group",
                        "is_irregular": True,
                        "can_have_cod": False,
                        "can_have_coi": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "last_used_at": "2024-01-15T16:45:00Z",
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
                        "path": "/verbs/nonexistent",
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
                        "path": "/verbs/parler",
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
) -> Verb:
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

        return verb

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting verb by infinitive {infinitive}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verb",
        )


@router.get(
    "/{infinitive}/conjugations",
    response_model=VerbWithConjugations,
    summary="Get verb conjugations for all tenses",
    description="""
    Retrieve comprehensive conjugation information for a specific French verb.

    **Returns**: Complete conjugation tables for all supported tenses:
    - Present (présent)
    - Past Composite (passé composé)
    - Imperfect (imparfait)
    - Future Simple (futur simple)
    - Conditional (conditionnel)
    - Subjunctive (subjonctif)
    - Imperative (impératif)

    **URL Encoding**: Supports URL encoding for verbs with spaces (e.g., "se%20lever" for "se lever")

    **Required Permission**: `read`, `write`, or `admin`
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
) -> VerbWithConjugations:
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

        return verb_with_conjugations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting verb conjugations for {infinitive}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verb conjugations",
        )
