"""Sentence-related schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from strenum import StrEnum

# Import Tense from verb schemas (reusing existing type)
from src.schemas.verbs import Tense


class Pronoun(StrEnum):
    """French pronouns."""

    FIRST_PERSON = "first_person"
    SECOND_PERSON = "second_person"
    THIRD_PERSON = "third_person"
    FIRST_PERSON_PLURAL = "first_person_plural"
    SECOND_PERSON_PLURAL = "second_person_plural"
    THIRD_PERSON_PLURAL = "third_person_plural"


class DirectObject(StrEnum):
    """Direct object types."""

    NONE = "none"
    MASCULINE = "masculine"
    FEMININE = "feminine"
    PLURAL = "plural"


class IndirectObject(StrEnum):
    """Indirect object types."""

    NONE = "none"
    MASCULINE = "masculine"
    FEMININE = "feminine"
    PLURAL = "plural"


class Negation(StrEnum):
    """Negation types."""

    NONE = "none"
    PAS = "pas"
    JAMAIS = "jamais"
    RIEN = "rien"
    PERSONNE = "personne"
    PLUS = "plus"
    AUCUN = "aucun"
    AUCUNE = "aucune"
    ENCORE = "encore"


class SentenceBase(BaseModel):
    """Base sentence schema with core fields."""

    target_language_code: str = "eng"
    content: str
    translation: str
    verb_id: UUID
    pronoun: Pronoun
    tense: Tense
    direct_object: DirectObject
    indirect_object: IndirectObject
    negation: Negation
    is_correct: bool = True
    explanation: str | None = None
    source: str | None = None

    @field_validator("target_language_code")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validate language code format: 3 chars (ISO 639-3)"""
        if not v:
            raise ValueError("Language code cannot be empty")

        # Convert to lowercase for consistency
        v = v.lower()

        # Check for standard ISO 639-3 format (3 characters)
        if len(v) == 3 and v.isalpha():
            return v

        raise ValueError(
            "Language code must be 3 characters (ISO 639-3 format, e.g., 'eng')"
        )


class SentenceCreate(SentenceBase):
    """Schema for creating a sentence."""

    pass


class SentenceUpdate(BaseModel):
    """Schema for updating a sentence."""

    target_language_code: str | None = None
    content: str | None = None
    translation: str | None = None
    verb_id: UUID | None = None
    pronoun: Pronoun | None = None
    tense: Tense | None = None
    direct_object: DirectObject | None = None
    indirect_object: IndirectObject | None = None
    negation: Negation | None = None
    is_correct: bool | None = None
    explanation: str | None = None
    source: str | None = None

    @field_validator("target_language_code")
    @classmethod
    def validate_language_code(cls, v: str | None) -> str | None:
        if v is None:
            return v

        if not v:
            raise ValueError("Language code cannot be empty")

        v = v.lower()
        if len(v) == 3 and v.isalpha():
            return v

        raise ValueError(
            "Language code must be 3 characters (ISO 639-3 format, e.g., 'eng')"
        )


class Sentence(SentenceBase):
    """Complete sentence schema with ID and timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CorrectnessValidationResponse(BaseModel):
    """Response schema for sentence correctness validation."""

    is_valid: bool
    explanation: str | None = None
    actual_direct_object: DirectObject
    actual_indirect_object: IndirectObject
    actual_negation: Negation
    direct_object_text: str | None = None
    indirect_object_text: str | None = None

    model_config = ConfigDict(from_attributes=True)
