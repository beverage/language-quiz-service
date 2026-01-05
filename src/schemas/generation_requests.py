"""
Generation request schema definitions.

Tracks async entity generation requests (problems, sentences, etc.) with status and results.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenerationStatus(str, Enum):
    """Status of a generation request."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    EXPIRED = "expired"  # Timed out waiting to be processed


class EntityType(str, Enum):
    """Type of entity being generated."""

    PROBLEM = "problem"
    SENTENCE = "sentence"
    VOCABULARY = "vocabulary"


class GenerationRequestBase(BaseModel):
    """Base generation request model with common fields."""

    entity_type: EntityType
    requested_count: int = Field(..., ge=1)
    constraints: dict[str, Any] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)


class GenerationRequestCreate(GenerationRequestBase):
    """Model for creating new generation requests."""

    status: GenerationStatus = Field(default=GenerationStatus.PENDING)
    generated_count: int = Field(default=0)
    failed_count: int = Field(default=0)


class GenerationRequest(GenerationRequestBase):
    """Complete generation request model with database fields."""

    id: UUID
    status: GenerationStatus
    generated_count: int
    failed_count: int
    requested_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
