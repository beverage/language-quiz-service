"""Verb-related schemas."""

from pydantic import BaseModel
from typing import Optional
from strenum import StrEnum


class Tense(StrEnum):
    """French verb tenses."""

    PRESENT = "present"
    PASSE_COMPOSE = "passe_compose"
    IMPARFAIT = "imparfait"
    FUTURE_SIMPLE = "future_simple"
    CONDITIONNEL = "conditionnel"
    SUBJUNCTIVE = "subjunctive"
    IMPERATIVE = "imperative"


class VerbBase(BaseModel):
    """Base verb schema."""

    infinitive: str
    auxiliary: str
    reflexive: bool = False


class Verb(VerbBase):
    """Complete verb schema with ID."""

    id: int

    class Config:
        from_attributes = True


class VerbCreate(VerbBase):
    """Schema for creating a verb."""

    infinitive: str
    auxiliary: str
    reflexive: bool


class VerbUpdate(VerbBase):
    """Schema for updating a verb."""

    infinitive: Optional[str] = None
    auxiliary: Optional[str] = None
    reflexive: Optional[bool] = None


class ConjugationBase(BaseModel):
    """Base conjugation schema."""

    verb_id: int
    tense: Tense
    infinitive: str
    first_person_singular: Optional[str] = None
    second_person_singular: Optional[str] = None
    third_person_singular: Optional[str] = None
    first_person_plural: Optional[str] = None
    second_person_formal: Optional[str] = None
    third_person_plural: Optional[str] = None


class Conjugation(ConjugationBase):
    """Complete conjugation schema with ID."""

    id: int

    class Config:
        from_attributes = True


class ConjugationCreate(ConjugationBase):
    """Schema for creating a conjugation."""

    pass


class VerbGroup(BaseModel):
    """Verb group classification schema."""

    id: int
    name: str
    example: str
    suffix: str
    classification: int  # 1, 2, or 3

    class Config:
        from_attributes = True
