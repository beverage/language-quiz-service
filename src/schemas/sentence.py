"""Sentence-related schemas."""

from pydantic import BaseModel
from enum import StrEnum
from .verb import Tense


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


class Sentence(SentenceBase):
    """Complete sentence schema with ID."""

    id: int
