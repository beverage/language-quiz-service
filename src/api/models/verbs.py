"""
Verb API request and response models.

These models define the API contracts for verb-related endpoints,
separate from internal service schemas to allow independent evolution.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.verbs import AuxiliaryType, VerbClassification


class VerbDownloadRequest(BaseModel):
    """
    Request model for downloading a verb from AI service.

    This endpoint uses AI to generate comprehensive verb information including
    conjugations, auxiliary verb information, participle forms, and translations.
    """

    infinitive: str = Field(
        ...,
        min_length=1,
        description="French verb in infinitive form",
        json_schema_extra={
            "examples": ["parler", "être", "avoir", "se lever"],
            "pattern": "^[a-zA-ZÀ-ÿ\\s]+$",
        },
    )
    target_language_code: str = Field(
        default="eng",
        description="Target language code for translation (ISO 639-3 format)",
        json_schema_extra={
            "examples": ["eng", "spa", "fra", "deu"],
            "pattern": "^[a-z]{3}$",
        },
    )

    class Config:
        json_schema_extra = {
            "example": {"infinitive": "parler", "target_language_code": "eng"}
        }


class VerbResponse(BaseModel):
    """
    API response model for verb data.

    Contains complete verb information including metadata, participles,
    classification, and grammatical properties.
    """

    id: UUID = Field(
        ...,
        description="Unique verb identifier",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    infinitive: str = Field(
        ..., description="Verb infinitive form", json_schema_extra={"example": "parler"}
    )
    auxiliary: AuxiliaryType = Field(
        ...,
        description="Auxiliary verb used in compound tenses (avoir or être)",
        json_schema_extra={"example": "avoir"},
    )
    reflexive: bool = Field(
        ...,
        description="Whether the verb is reflexive (uses reflexive pronouns)",
        json_schema_extra={"example": False},
    )
    target_language_code: str = Field(
        ...,
        description="ISO 639-3 target language code for translation",
        json_schema_extra={"example": "eng"},
    )
    translation: str = Field(
        ...,
        description="Translation of the verb in the target language",
        json_schema_extra={"example": "to speak"},
    )
    past_participle: str = Field(
        ...,
        description="Past participle form (used in compound tenses)",
        json_schema_extra={"example": "parlé"},
    )
    present_participle: str = Field(
        ...,
        description="Present participle form (gerund form)",
        json_schema_extra={"example": "parlant"},
    )
    classification: VerbClassification | None = Field(
        None,
        description="French verb group classification (1st, 2nd, or 3rd group)",
        json_schema_extra={"example": "first_group"},
    )
    is_irregular: bool = Field(
        ...,
        description="Whether the verb has irregular conjugation patterns",
        json_schema_extra={"example": False},
    )
    can_have_cod: bool = Field(
        ...,
        description="Whether the verb can take a direct object (COD)",
        json_schema_extra={"example": True},
    )
    can_have_coi: bool = Field(
        ...,
        description="Whether the verb can take an indirect object (COI)",
        json_schema_extra={"example": True},
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the verb was first created in the database"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the verb was last updated"
    )
    last_used_at: datetime | None = Field(
        None, description="Timestamp when the verb was last accessed (for analytics)"
    )

    class Config:
        json_schema_extra = {
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
                "can_have_cod": True,
                "can_have_coi": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_used_at": "2024-01-15T16:45:00Z",
            }
        }


class ConjugationResponse(BaseModel):
    """
    API response model for verb conjugation data.

    Contains all conjugated forms for a specific tense, including
    all persons (je, tu, il/elle, nous, vous, ils/elles).
    """

    id: UUID = Field(
        ...,
        description="Unique conjugation identifier",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174001"},
    )
    infinitive: str = Field(
        ...,
        description="Base verb infinitive form",
        json_schema_extra={"example": "parler"},
    )
    auxiliary: AuxiliaryType = Field(
        ...,
        description="Auxiliary verb (avoir or être)",
        json_schema_extra={"example": "avoir"},
    )
    reflexive: bool = Field(
        ...,
        description="Whether this conjugation is for a reflexive verb",
        json_schema_extra={"example": False},
    )
    tense: str = Field(
        ...,
        description="French verb tense for this conjugation",
        json_schema_extra={
            "example": "present",
            "enum": [
                "present",
                "passe_compose",
                "imparfait",
                "future_simple",
                "conditionnel",
                "subjonctif",
                "imperatif",
            ],
        },
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
    created_at: datetime = Field(
        ..., description="Timestamp when the conjugation was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the conjugation was last updated"
    )

    class Config:
        json_schema_extra = {
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
        }


class VerbWithConjugationsResponse(VerbResponse):
    """
    API response model for verb with all its conjugations.

    Extends VerbResponse to include complete conjugation tables
    for all supported tenses.
    """

    conjugations: list[ConjugationResponse] = Field(
        default_factory=list,
        description="Complete list of conjugations for all tenses",
        json_schema_extra={
            "description": "Array containing conjugation objects for each tense (present, passé composé, imparfait, etc.)"
        },
    )

    class Config:
        json_schema_extra = {
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
                "can_have_cod": True,
                "can_have_coi": True,
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
                    },
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "infinitive": "parler",
                        "auxiliary": "avoir",
                        "reflexive": False,
                        "tense": "imparfait",
                        "first_person_singular": "parlais",
                        "second_person_singular": "parlais",
                        "third_person_singular": "parlait",
                        "first_person_plural": "parlions",
                        "second_person_plural": "parliez",
                        "third_person_plural": "parlaient",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                    },
                ],
            }
        }
