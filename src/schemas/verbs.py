"""
Pydantic schemas for French verbs and conjugations.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuxiliaryType(str, Enum):
    """Auxiliary verb types for French verbs."""

    AVOIR = "avoir"
    ETRE = "être"


class VerbClassification(str, Enum):
    """French verb group classifications."""

    FIRST_GROUP = "first_group"
    SECOND_GROUP = "second_group"
    THIRD_GROUP = "third_group"


class Tense(str, Enum):
    """French verb tenses."""

    PRESENT = "present"
    PASSE_COMPOSE = "passe_compose"
    PLUS_QUE_PARFAIT = "plus_que_parfait"
    IMPARFAIT = "imparfait"
    FUTURE_SIMPLE = "future_simple"
    CONDITIONNEL = "conditionnel"
    SUBJONCTIF = "subjonctif"
    IMPERATIF = "imperatif"


class VerbBase(BaseModel):
    """Base verb fields for create/update operations."""

    infinitive: str = Field(
        ...,
        description="Verb infinitive form",
        json_schema_extra={"example": "parler"},
        min_length=1,
    )
    auxiliary: AuxiliaryType = Field(
        ...,
        description="Auxiliary verb (avoir or être)",
        json_schema_extra={"example": "avoir"},
    )
    reflexive: bool = Field(
        default=False,
        description="Whether the verb is reflexive",
        json_schema_extra={"example": False},
    )
    target_language_code: str = Field(
        ...,
        description="ISO 639-3 source language code",
        json_schema_extra={"example": "eng"},
    )
    translation: str = Field(
        ...,
        description="English translation of the verb",
        json_schema_extra={"example": "to speak"},
        min_length=1,
    )
    past_participle: str = Field(
        ...,
        description="Past participle form",
        json_schema_extra={"example": "parlé"},
        min_length=1,
    )
    present_participle: str = Field(
        ...,
        description="Present participle form",
        json_schema_extra={"example": "parlant"},
        min_length=1,
    )
    classification: VerbClassification | None = Field(
        None,
        description="French verb group classification",
        json_schema_extra={"example": "first_group"},
    )
    is_irregular: bool = Field(
        default=False,
        description="Whether the verb has irregular conjugations",
        json_schema_extra={"example": False},
    )
    can_have_cod: bool = Field(
        default=True,
        description="Whether the verb can have a direct object",
        json_schema_extra={"example": True},
    )
    can_have_coi: bool = Field(
        default=True,
        description="Whether the verb can have an indirect object",
        json_schema_extra={"example": True},
    )
    is_test: bool = Field(
        default=False,
        description="Flag for test data - excluded from random selection",
        json_schema_extra={"example": False},
    )

    @field_validator(
        "infinitive", "translation", "past_participle", "present_participle"
    )
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

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


class VerbCreate(VerbBase):
    """Schema for creating a new verb."""

    pass


class VerbUpdate(BaseModel):
    """Schema for updating an existing verb."""

    infinitive: str | None = Field(None, min_length=1)
    auxiliary: AuxiliaryType | None = None
    reflexive: bool | None = None
    target_language_code: str | None = None
    translation: str | None = Field(None, min_length=1)
    past_participle: str | None = Field(None, min_length=1)
    present_participle: str | None = Field(None, min_length=1)
    classification: VerbClassification | None = None
    is_irregular: bool | None = None
    can_have_cod: bool | None = None
    can_have_coi: bool | None = None
    is_test: bool | None = None

    @field_validator(
        "infinitive", "translation", "past_participle", "present_participle"
    )
    @classmethod
    def text_must_not_be_empty(cls, v: str | None) -> str | None:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Text cannot be empty")
        return v.strip() if v else v

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


class Verb(VerbBase):
    """Complete verb schema with database fields."""

    id: UUID = Field(
        ...,
        description="Unique verb identifier",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    created_at: datetime = Field(..., description="Timestamp when verb was created")
    updated_at: datetime = Field(
        ..., description="Timestamp when verb was last updated"
    )
    last_used_at: datetime | None = Field(
        None, description="Timestamp when verb was last used"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
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
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_used_at": None,
            }
        },
    )


class ConjugationBase(BaseModel):
    """Base conjugation fields for create/update operations."""

    infinitive: str = Field(
        ...,
        description="Verb infinitive form",
        json_schema_extra={"example": "parler"},
        min_length=1,
    )
    auxiliary: AuxiliaryType = Field(
        ...,
        description="Auxiliary verb (avoir or être)",
        json_schema_extra={"example": "avoir"},
    )
    reflexive: bool = Field(
        default=False,
        description="Whether the verb is reflexive",
        json_schema_extra={"example": False},
    )
    tense: Tense = Field(
        ..., description="Verb tense", json_schema_extra={"example": "present"}
    )
    first_person_singular: str | None = Field(
        None,
        description="First person singular form (je)",
        json_schema_extra={"example": "parle"},
    )
    second_person_singular: str | None = Field(
        None,
        description="Second person singular form (tu)",
        json_schema_extra={"example": "parles"},
    )
    third_person_singular: str | None = Field(
        None,
        description="Third person singular form (il/elle)",
        json_schema_extra={"example": "parle"},
    )
    first_person_plural: str | None = Field(
        None,
        description="First person plural form (nous)",
        json_schema_extra={"example": "parlons"},
    )
    second_person_plural: str | None = Field(
        None,
        description="Second person plural form (vous)",
        json_schema_extra={"example": "parlez"},
    )
    third_person_plural: str | None = Field(
        None,
        description="Third person plural form (ils/elles)",
        json_schema_extra={"example": "parlent"},
    )

    @field_validator("infinitive")
    @classmethod
    def infinitive_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Infinitive cannot be empty")
        return v.strip()


class LLMVerbPayload(VerbBase):
    tenses: list[ConjugationBase] = []  # Default to empty list when not provided


class ConjugationCreate(ConjugationBase):
    """Schema for creating a new conjugation."""

    pass


class ConjugationUpdate(BaseModel):
    """Schema for updating an existing conjugation."""

    infinitive: str | None = Field(None, min_length=1)
    auxiliary: AuxiliaryType | None = None
    reflexive: bool | None = None
    tense: Tense | None = None
    first_person_singular: str | None = None
    second_person_singular: str | None = None
    third_person_singular: str | None = None
    first_person_plural: str | None = None
    second_person_plural: str | None = None
    third_person_plural: str | None = None

    @field_validator("infinitive")
    @classmethod
    def infinitive_must_not_be_empty(cls, v: str | None) -> str | None:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Infinitive cannot be empty")
        return v.strip() if v else v


class Conjugation(ConjugationBase):
    """Complete conjugation schema with database fields."""

    id: UUID = Field(
        ...,
        description="Unique conjugation identifier",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174001"},
    )
    created_at: datetime = Field(
        ..., description="Timestamp when conjugation was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when conjugation was last updated"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "infinitive": "parler",
                "auxiliary": "avoir",
                "reflexive": False,
                "tense": "present",
                "first_person_singular": "parle",
                "second_person_singular": "parles",
                "third_person_singular": "parle",
                "first_person_plural": "parlons",
                "second_person_plural": "parlez",
                "third_person_plural": "parlent",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    )


class VerbWithConjugations(Verb):
    """Verb schema with associated conjugations."""

    conjugations: list[Conjugation] = Field(
        default_factory=list, description="All conjugations for this verb"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
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
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_used_at": None,
                "conjugations": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174001",
                        "infinitive": "parler",
                        "auxiliary": "avoir",
                        "reflexive": False,
                        "tense": "present",
                        "first_person_singular": "parle",
                        "second_person_singular": "parles",
                        "third_person_singular": "parle",
                        "first_person_plural": "parlons",
                        "second_person_plural": "parlez",
                        "third_person_plural": "parlent",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                    }
                ],
            }
        },
    )
