"""Generation request endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.models.generation_requests import GenerationRequestResponse
from src.api.models.problems import ProblemResponse
from src.core.auth import get_current_api_key
from src.services.generation_request_service import GenerationRequestService

logger = logging.getLogger(__name__)

API_PREFIX = "/generation-requests"
router = APIRouter(prefix=API_PREFIX, tags=["Generation Requests"])


async def get_generation_request_service() -> GenerationRequestService:
    """Dependency to get GenerationRequestService instance."""
    return GenerationRequestService()


@router.get(
    "/{request_id}",
    response_model=GenerationRequestResponse,
    summary="Get generation request status and results",
    description="""
    Retrieve the status and results of an async generation request.

    This endpoint returns:
    - **Request metadata**: Status, counts, timestamps
    - **Generated entities**: Full problem objects created by the request

    Use this to check the status of async generation requests and retrieve
    the generated problems once complete.

    **Required Permission**: `read`, `write`, or `admin`
    """,
    responses={
        200: {
            "description": "Generation request retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "entity_type": "problem",
                        "status": "completed",
                        "requested_at": "2025-11-16T10:30:00Z",
                        "completed_at": "2025-11-16T10:32:15Z",
                        "requested_count": 5,
                        "generated_count": 5,
                        "failed_count": 0,
                        "entities": [
                            {"id": "...", "problem_type": "grammar"},
                        ],
                    }
                }
            },
        },
        404: {
            "description": "Generation request not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Generation request with ID ... not found",
                        "status_code": 404,
                    }
                }
            },
        },
    },
)
async def get_generation_request(
    request_id: UUID,
    current_key: dict = Depends(get_current_api_key),
    generation_request_service: GenerationRequestService = Depends(
        get_generation_request_service
    ),
) -> GenerationRequestResponse:
    """
    Get generation request by ID with all generated entities.

    Returns request metadata and full problem objects.
    """
    (
        generation_request,
        problems,
    ) = await generation_request_service.get_generation_request_with_entities(
        request_id
    )

    # Convert problems to response models
    problem_responses = [
        ProblemResponse.from_problem(problem, include_metadata=False)
        for problem in problems
    ]

    return GenerationRequestResponse(
        request_id=str(generation_request.id),
        entity_type=generation_request.entity_type,
        status=generation_request.status,
        requested_at=generation_request.requested_at.isoformat(),
        started_at=(
            generation_request.started_at.isoformat()
            if generation_request.started_at
            else None
        ),
        completed_at=(
            generation_request.completed_at.isoformat()
            if generation_request.completed_at
            else None
        ),
        requested_count=generation_request.requested_count,
        generated_count=generation_request.generated_count,
        failed_count=generation_request.failed_count,
        constraints=generation_request.constraints,
        error_message=generation_request.error_message,
        entities=problem_responses,
    )
