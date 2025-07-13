"""Sentence-related schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
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


class IndirectPronoun(StrEnum):
    """Indirect pronoun types."""

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

    target_language_code: str = "en"
    content: str
    translation: str
    verb_id: UUID
    pronoun: Pronoun
    tense: Tense
    direct_object: DirectObject
    indirect_pronoun: IndirectPronoun
    negation: Negation
    is_correct: bool = True
    explanation: Optional[str] = None
    source: Optional[str] = None


class SentenceCreate(SentenceBase):
    """Schema for creating a sentence."""

    pass


class SentenceUpdate(BaseModel):
    """Schema for updating a sentence."""

    target_language_code: Optional[str] = None
    content: Optional[str] = None
    translation: Optional[str] = None
    verb_id: Optional[UUID] = None
    pronoun: Optional[Pronoun] = None
    tense: Optional[Tense] = None
    direct_object: Optional[DirectObject] = None
    indirect_pronoun: Optional[IndirectPronoun] = None
    negation: Optional[Negation] = None
    is_correct: Optional[bool] = None
    explanation: Optional[str] = None
    source: Optional[str] = None


class Sentence(SentenceBase):
    """Complete sentence schema with ID and timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
