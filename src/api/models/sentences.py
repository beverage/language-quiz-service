"""
Sentence API request and response models.

These models define the API contracts for sentence-related endpoints,
providing clean separation from internal service schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
)
from src.schemas.verbs import Tense


class SentenceGenerateRequest(BaseModel):
    """
    Request schema for AI sentence generation.

    Used for generating French sentences with specific grammatical parameters
    using AI services. All parameters control the grammatical structure
    of the generated sentence.
    """

    verb_infinitive: str = Field(
        ...,
        description="French verb infinitive to use in sentence generation",
        json_schema_extra={
            "examples": ["parler", "être", "avoir", "se lever"],
            "pattern": "^[a-zA-ZÀ-ÿ\\s]+$",
        },
    )
    pronoun: Pronoun = Field(
        default=Pronoun.FIRST_PERSON,
        description="Subject pronoun for the sentence (je, tu, il/elle, nous, vous, ils/elles)",
        json_schema_extra={"example": "first_person"},
    )
    tense: Tense = Field(
        default=Tense.PRESENT,
        description="Verb tense to use in the sentence",
        json_schema_extra={
            "example": "present",
            "enum": [
                "present",
                "passe_compose",
                "plus_que_parfait",
                "imparfait",
                "future_simple",
                "conditionnel",
                "subjonctif",
                "imperatif",
            ],
        },
    )
    direct_object: DirectObject = Field(
        default=DirectObject.NONE,
        description="Type of direct object to include (none, masculine, feminine, plural)",
        json_schema_extra={"example": "none"},
    )
    indirect_object: IndirectObject = Field(
        default=IndirectObject.NONE,
        description="Type of indirect object to include (none, person, thing)",
        json_schema_extra={"example": "none"},
    )
    negation: Negation = Field(
        default=Negation.NONE,
        description="Type of negation to apply (none, pas, jamais, rien, etc.)",
        json_schema_extra={
            "example": "none",
            "enum": [
                "none",
                "pas",
                "jamais",
                "rien",
                "personne",
                "plus",
                "aucun",
                "aucune",
                "encore",
            ],
        },
    )
    is_correct: bool = Field(
        default=True,
        description="Whether to generate a grammatically correct sentence (true) or incorrect for testing (false)",
        json_schema_extra={"example": True},
    )
    target_language_code: str = Field(
        default="eng",
        description="Target language code for translation (ISO 639-3 format)",
        json_schema_extra={
            "examples": ["eng", "spa", "fra", "deu"],
            "pattern": "^[a-z]{3}$",
        },
    )

    @field_validator("verb_infinitive")
    @classmethod
    def validate_infinitive(cls, v: str) -> str:
        """Validate verb infinitive is not empty."""
        if not v or not v.strip():
            raise ValueError("Verb infinitive cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "verb_infinitive": "parler",
                "pronoun": "first_person",
                "tense": "present",
                "direct_object": "masculine",
                "indirect_object": "none",
                "negation": "none",
                "is_correct": True,
                "target_language_code": "eng",
            }
        }
    )


class SentenceListRequest(BaseModel):
    """
    Request schema for listing sentences with filters.

    All fields are optional and used to filter the sentence results.
    Combine multiple filters to narrow down results.
    """

    verb_id: UUID | None = Field(
        None,
        description="Filter sentences by specific verb UUID",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    is_correct: bool | None = Field(
        None,
        description="Filter by sentence correctness (true for correct, false for incorrect sentences)",
        json_schema_extra={"example": True},
    )
    tense: str | None = Field(
        None,
        description="Filter by verb tense used in sentences",
        json_schema_extra={
            "example": "present",
            "enum": [
                "present",
                "passe_compose",
                "plus_que_parfait",
                "imparfait",
                "future_simple",
                "conditionnel",
                "subjonctif",
                "imperatif",
            ],
        },
    )
    pronoun: str | None = Field(
        None,
        description="Filter by pronoun used in sentences",
        json_schema_extra={
            "example": "first_person",
            "enum": [
                "first_person",
                "second_person",
                "third_person",
                "first_person_plural",
                "second_person_plural",
                "third_person_plural",
            ],
        },
    )
    target_language_code: str | None = Field(
        None,
        description="Filter by target language code for translations",
        json_schema_extra={"example": "eng", "pattern": "^[a-z]{3}$"},
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of sentences to return (1-100)",
        json_schema_extra={"example": 25},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "verb_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_correct": True,
                "tense": "present",
                "pronoun": "first_person",
                "target_language_code": "eng",
                "limit": 25,
            }
        }
    )


class SentenceResponse(BaseModel):
    """
    API response model for sentence data.

    Contains complete sentence information including the French content,
    translation, grammatical metadata, and validation information.
    """

    id: UUID = Field(
        ...,
        description="Unique sentence identifier",
        json_schema_extra={"example": "789e1234-e89b-12d3-a456-426614174333"},
    )
    target_language_code: str = Field(
        ...,
        description="ISO 639-3 language code for the translation",
        json_schema_extra={"example": "eng"},
    )
    content: str = Field(
        ...,
        description="The French sentence content",
        json_schema_extra={"example": "Je parle français tous les jours."},
    )
    translation: str = Field(
        ...,
        description="Translation of the sentence in the target language",
        json_schema_extra={"example": "I speak French every day."},
    )
    verb_id: UUID = Field(
        ...,
        description="UUID of the verb used in this sentence",
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    pronoun: Pronoun = Field(
        ...,
        description="Subject pronoun used in the sentence",
        json_schema_extra={"example": "first_person"},
    )
    tense: Tense = Field(
        ...,
        description="Verb tense used in the sentence",
        json_schema_extra={"example": "present"},
    )
    direct_object: DirectObject = Field(
        ...,
        description="Type of direct object present in the sentence",
        json_schema_extra={"example": "masculine"},
    )
    indirect_object: IndirectObject = Field(
        ...,
        description="Type of indirect object present in the sentence",
        json_schema_extra={"example": "none"},
    )
    negation: Negation = Field(
        ...,
        description="Type of negation used in the sentence",
        json_schema_extra={"example": "none"},
    )
    is_correct: bool = Field(
        ...,
        description="Whether the sentence is grammatically correct",
        json_schema_extra={"example": True},
    )
    explanation: str | None = Field(
        None,
        description="Optional explanation of grammatical features or corrections",
        json_schema_extra={
            "example": "This sentence uses the present tense with a direct object complement."
        },
    )
    source: str | None = Field(
        None,
        description="Source of the sentence (e.g., 'AI_GENERATED', 'MANUAL_ENTRY')",
        json_schema_extra={"example": "AI_GENERATED"},
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the sentence was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the sentence was last updated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "789e1234-e89b-12d3-a456-426614174333",
                "target_language_code": "eng",
                "content": "Je parle français tous les jours.",
                "translation": "I speak French every day.",
                "verb_id": "123e4567-e89b-12d3-a456-426614174000",
                "pronoun": "first_person",
                "tense": "present",
                "direct_object": "masculine",
                "indirect_object": "none",
                "negation": "none",
                "is_correct": True,
                "explanation": "This sentence uses the present tense with a direct object complement.",
                "source": "AI_GENERATED",
                "created_at": "2024-01-15T11:30:00Z",
                "updated_at": "2024-01-15T11:30:00Z",
            }
        }
    )
