"""API models for generation request endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class GenerationRequestResponse(BaseModel):
    """Response model for generation request queries."""

    request_id: str = Field(..., description="UUID of the generation request")
    entity_type: str = Field(..., description="Type of entities being generated")
    status: str = Field(..., description="Current status of the generation request")
    requested_at: str = Field(
        ..., description="ISO 8601 timestamp when request was created"
    )
    started_at: str | None = Field(
        None, description="ISO 8601 timestamp when processing started"
    )
    completed_at: str | None = Field(
        None, description="ISO 8601 timestamp when request completed"
    )
    requested_count: int = Field(..., description="Number of entities requested")
    generated_count: int = Field(
        ..., description="Number of entities successfully generated"
    )
    failed_count: int = Field(
        ..., description="Number of entities that failed to generate"
    )
    constraints: dict[str, Any] | None = Field(
        None, description="Original generation constraints"
    )
    error_message: str | None = Field(
        None, description="Error message if request failed"
    )
    entities: list[Any] = Field(..., description="Array of generated entity objects")
