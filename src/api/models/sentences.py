"""
Sentence API request and response models.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
)
from src.schemas.verbs import Tense


class SentenceGenerateRequest(BaseModel):
    """Request schema for AI sentence generation."""
    
    verb_infinitive: str
    pronoun: Pronoun = Pronoun.FIRST_PERSON
    tense: Tense = Tense.PRESENT
    direct_object: DirectObject = DirectObject.NONE
    indirect_object: IndirectObject = IndirectObject.NONE
    negation: Negation = Negation.NONE
    is_correct: bool = True
    target_language_code: str = "eng"
    
    @field_validator("verb_infinitive")
    @classmethod
    def validate_infinitive(cls, v: str) -> str:
        """Validate verb infinitive is not empty."""
        if not v or not v.strip():
            raise ValueError("Verb infinitive cannot be empty")
        return v.strip()


class SentenceListRequest(BaseModel):
    """Request schema for listing sentences with filters."""
    
    verb_id: Optional[UUID] = None
    is_correct: Optional[bool] = None
    tense: Optional[str] = None
    pronoun: Optional[str] = None
    target_language_code: Optional[str] = None
    limit: int = 50


class SentenceResponse(BaseModel):
    """API response model for sentence data."""

    id: UUID
    target_language_code: str
    content: str
    translation: str
    verb_id: UUID
    pronoun: Pronoun
    tense: Tense
    direct_object: DirectObject
    indirect_object: IndirectObject
    negation: Negation
    is_correct: bool
    explanation: str | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime 