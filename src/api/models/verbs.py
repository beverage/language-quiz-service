"""
Verb API request and response models.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.verbs import AuxiliaryType, VerbClassification


class VerbDownloadRequest(BaseModel):
    """Request model for verb download."""

    infinitive: str = Field(
        ..., min_length=1, description="French verb in infinitive form"
    )
    target_language_code: str = Field(
        default="eng", description="Target language code (ISO 639-3)"
    )


class VerbResponse(BaseModel):
    """API response model for verb data."""

    id: UUID = Field(
        ...,
        description="Unique verb identifier",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    infinitive: str = Field(
        ...,
        description="Verb infinitive form",
        json_schema_extra={"example": "parler"},
    )
    auxiliary: AuxiliaryType = Field(
        ...,
        description="Auxiliary verb (avoir or être)",
        json_schema_extra={"example": "avoir"},
    )
    reflexive: bool = Field(
        ...,
        description="Whether the verb is reflexive",
        json_schema_extra={"example": False},
    )
    target_language_code: str = Field(
        ...,
        description="ISO 639-3 target language code",
        json_schema_extra={"example": "eng"},
    )
    translation: str = Field(
        ...,
        description="Translation of the verb",
        json_schema_extra={"example": "to speak"},
    )
    past_participle: str = Field(
        ...,
        description="Past participle form",
        json_schema_extra={"example": "parlé"},
    )
    present_participle: str = Field(
        ...,
        description="Present participle form",
        json_schema_extra={"example": "parlant"},
    )
    classification: VerbClassification | None = Field(
        None,
        description="French verb group classification",
        json_schema_extra={"example": "first_group"},
    )
    is_irregular: bool = Field(
        ...,
        description="Whether the verb has irregular conjugations",
        json_schema_extra={"example": False},
    )
    can_have_cod: bool = Field(
        ...,
        description="Whether the verb can have a direct object",
        json_schema_extra={"example": True},
    )
    can_have_coi: bool = Field(
        ...,
        description="Whether the verb can have an indirect object",
        json_schema_extra={"example": True},
    )
    created_at: datetime = Field(..., description="Timestamp when verb was created")
    updated_at: datetime = Field(
        ..., description="Timestamp when verb was last updated"
    )
    last_used_at: datetime | None = Field(
        None, description="Timestamp when verb was last used"
    )


class ConjugationResponse(BaseModel):
    """API response model for conjugation data."""

    id: UUID = Field(
        ...,
        description="Unique conjugation identifier",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174001"},
    )
    infinitive: str = Field(
        ...,
        description="Verb infinitive form",
        json_schema_extra={"example": "parler"},
    )
    auxiliary: AuxiliaryType = Field(
        ...,
        description="Auxiliary verb (avoir or être)",
        json_schema_extra={"example": "avoir"},
    )
    reflexive: bool = Field(
        ...,
        description="Whether the verb is reflexive",
        json_schema_extra={"example": False},
    )
    tense: str = Field(
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
    created_at: datetime = Field(
        ..., description="Timestamp when conjugation was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when conjugation was last updated"
    )


class VerbWithConjugationsResponse(VerbResponse):
    """API response model for verb with all conjugations."""

    conjugations: list[ConjugationResponse] = Field(
        default_factory=list, description="All conjugations for this verb"
    ) 