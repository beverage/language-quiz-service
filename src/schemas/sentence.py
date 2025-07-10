"""Sentence-related schemas."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum
from .verb import Tense


class Pronoun(str, Enum):
    """French pronouns."""

    FIRST_PERSON = "first_person"
    SECOND_PERSON = "second_person"
    THIRD_PERSON = "third_person"
    FIRST_PERSON_PLURAL = "first_person_plural"
    SECOND_PERSON_PLURAL = "second_person_plural"
    THIRD_PERSON_PLURAL = "third_person_plural"


class DirectObject(str, Enum):
    """Direct object types."""

    NONE = "none"
    MASCULINE = "masculine"
    FEMININE = "feminine"
    PLURAL = "plural"


class IndirectPronoun(str, Enum):
    """Indirect pronoun types."""

    NONE = "none"
    MASCULINE = "masculine"
    FEMININE = "feminine"
    PLURAL = "plural"


class Negation(str, Enum):
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
    """Base sentence schema."""

    infinitive: str
    auxiliary: str
    pronoun: Pronoun
    tense: Tense
    direct_object: DirectObject
    indirect_pronoun: IndirectPronoun
    negation: Negation
    content: str
    translation: str
    is_correct: bool = True


class SentenceCreate(SentenceBase):
    """Schema for creating a sentence."""

    pass


class SentenceUpdate(BaseModel):
    """Schema for updating a sentence."""

    infinitive: Optional[str] = None
    auxiliary: Optional[str] = None
    pronoun: Optional[Pronoun] = None
    tense: Optional[Tense] = None
    direct_object: Optional[DirectObject] = None
    indirect_pronoun: Optional[IndirectPronoun] = None
    negation: Optional[Negation] = None
    content: Optional[str] = None
    translation: Optional[str] = None
    is_correct: Optional[bool] = None


class Sentence(SentenceBase):
    """Complete sentence schema with ID."""

    id: int

    class Config:
        from_attributes = True
