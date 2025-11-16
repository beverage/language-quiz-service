"""
Problem schema definitions.

Following the established patterns from sentences and verbs schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProblemType(str, Enum):
    """Problem type categories."""

    GRAMMAR = "grammar"
    FUNCTIONAL = "functional"
    VOCABULARY = "vocabulary"


class DifficultyLevel(str, Enum):
    """Difficulty levels for problems."""

    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    NATIVE = "native"


# Base Problem model
class ProblemBase(BaseModel):
    """Base problem model with common fields."""

    problem_type: ProblemType
    title: str | None = None
    instructions: str
    correct_answer_index: int = Field(..., ge=0)
    target_language_code: str = Field(default="eng", max_length=3, min_length=3)
    statements: list[dict[str, Any]] = Field(..., min_length=1)
    topic_tags: list[str] = Field(default_factory=list)
    source_statement_ids: list[UUID] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)

    @field_validator("statements")
    @classmethod
    def validate_statements_structure(cls, v, info):
        """Validate statements structure based on problem type."""
        if not v:
            raise ValueError("statements cannot be empty")

        # Get problem_type from the input data
        problem_type = info.data.get("problem_type") if info.data else None
        if not problem_type:
            return v  # Can't validate without problem type

        if problem_type == ProblemType.GRAMMAR:
            return cls._validate_grammar_statements(v)
        elif problem_type == ProblemType.FUNCTIONAL:
            return cls._validate_functional_statements(v)
        elif problem_type == ProblemType.VOCABULARY:
            return cls._validate_vocabulary_statements(v)

        return v

    @model_validator(mode="after")
    def validate_correct_answer_index(self):
        """Ensure correct_answer_index is within bounds of statements array."""
        if hasattr(self, "statements") and hasattr(self, "correct_answer_index"):
            if self.correct_answer_index >= len(self.statements):
                raise ValueError(
                    "correct_answer_index must be less than number of statements"
                )
        return self

    @staticmethod
    def _validate_grammar_statements(
        statements: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Validate grammar problem statements."""
        for i, stmt in enumerate(statements):
            if "content" not in stmt:
                raise ValueError(f'Grammar statement {i} must have "content" field')
            if "is_correct" not in stmt:
                raise ValueError(f'Grammar statement {i} must have "is_correct" field')

            is_correct = stmt.get("is_correct")
            if is_correct and "translation" not in stmt:
                raise ValueError(
                    f'Correct grammar statement {i} must have "translation" field'
                )
            elif not is_correct and "explanation" not in stmt:
                raise ValueError(
                    f'Incorrect grammar statement {i} must have "explanation" field'
                )

        return statements

    @staticmethod
    def _validate_functional_statements(
        statements: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Validate functional problem statements."""
        for i, stmt in enumerate(statements):
            if "sentence" not in stmt:
                raise ValueError(f'Functional statement {i} must have "sentence" field')
            if "option" not in stmt:
                raise ValueError(f'Functional statement {i} must have "option" field')

        return statements

    @staticmethod
    def _validate_vocabulary_statements(
        statements: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Validate vocabulary problem statements."""
        for i, stmt in enumerate(statements):
            if "word" not in stmt:
                raise ValueError(f'Vocabulary statement {i} must have "word" field')
            if "definition" not in stmt:
                raise ValueError(
                    f'Vocabulary statement {i} must have "definition" field'
                )

        return statements


# Create model (for API input)
class ProblemCreate(ProblemBase):
    """Model for creating new problems."""

    request_id: UUID | None = None  # Optional correlation to generation request


# Update model (for API updates)
class ProblemUpdate(BaseModel):
    """Model for updating existing problems."""

    problem_type: ProblemType | None = None
    title: str | None = None
    instructions: str | None = None
    correct_answer_index: int | None = Field(None, ge=0)
    target_language_code: str | None = Field(None, max_length=3, min_length=3)
    statements: list[dict[str, Any]] | None = Field(None, min_length=1)
    topic_tags: list[str] | None = None
    source_statement_ids: list[UUID] | None = None
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_correct_answer_index(self):
        """Ensure correct_answer_index is within bounds if provided."""
        if (
            hasattr(self, "correct_answer_index")
            and self.correct_answer_index is not None
            and hasattr(self, "statements")
            and self.statements
        ):
            if self.correct_answer_index >= len(self.statements):
                raise ValueError(
                    "correct_answer_index must be less than number of statements"
                )
        return self


# Full model (from database)
class Problem(ProblemBase):
    """Complete problem model with database fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    last_served_at: datetime | None = None
    request_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


# Response models for specific use cases
class ProblemSummary(BaseModel):
    """Lightweight problem summary for lists."""

    id: UUID
    problem_type: ProblemType
    title: str | None = None
    instructions: str
    correct_answer_index: int
    topic_tags: list[str]
    created_at: datetime

    # Derived fields
    statement_count: int = Field(
        ..., description="Number of statements in this problem"
    )

    model_config = ConfigDict(from_attributes=True)


class ProblemWithMetadata(Problem):
    """Problem with enriched metadata for analytics."""

    # Derived fields that might be computed
    estimated_difficulty: str | None = None
    usage_count: int | None = None
    success_rate: float | None = None

    model_config = ConfigDict(from_attributes=True)


# Helper models for problem generation
class GrammarProblemConstraints(BaseModel):
    """Constraints for generating grammar problems."""

    grammatical_focus: list[str] = Field(
        default_factory=list,
        max_length=10,  # Max 10 focus items
        description="Grammatical concepts to focus on",
    )
    verb_infinitives: list[str] | None = Field(
        None,
        max_length=10,  # Max 10 verbs
        description="Specific verbs to use",
    )
    tenses_used: list[str] | None = Field(
        None,
        max_length=10,  # Max 10 tenses
        description="Specific tenses to use",
    )
    includes_negation: bool | None = None
    includes_cod: bool | None = None
    includes_coi: bool | None = None
    difficulty_level: DifficultyLevel | None = None

    @field_validator("grammatical_focus")
    @classmethod
    def validate_grammatical_focus_items(cls, v):
        """Validate each item in grammatical_focus."""
        if v:
            for item in v:
                if len(item) > 50:
                    raise ValueError(
                        "Each grammatical focus item must be <= 50 characters"
                    )
        return v

    @field_validator("verb_infinitives")
    @classmethod
    def validate_verb_infinitives_items(cls, v):
        """Validate each verb infinitive."""
        if v:
            for item in v:
                if len(item) > 30:
                    raise ValueError("Each verb infinitive must be <= 30 characters")
        return v

    @field_validator("tenses_used")
    @classmethod
    def validate_tenses_items(cls, v):
        """Validate each tense."""
        if v:
            for item in v:
                if len(item) > 30:
                    raise ValueError("Each tense must be <= 30 characters")
        return v


class FunctionalProblemConstraints(BaseModel):
    """Constraints for generating functional problems."""

    part_of_speech: str | None = None  # "adverb", "connector", "preposition"
    grammatical_function: str | None = None  # "negation", "logical_connection"
    function_category: str | None = None  # "temporal_negation", "causal_connection"
    target_construction: str | None = None  # "ne_jamais", "mais_opposition"
    difficulty_level: DifficultyLevel | None = None


class VocabularyProblemConstraints(BaseModel):
    """Constraints for generating vocabulary problems."""

    semantic_field: list[str] | None = None  # ["animals", "food"]
    word_difficulty: DifficultyLevel | None = None
    includes_pronunciation: bool | None = None
    word_type: str | None = None  # "noun", "verb", "adjective"


# Union type for problem constraints
ProblemConstraints = (
    GrammarProblemConstraints
    | FunctionalProblemConstraints
    | VocabularyProblemConstraints
)


# Query models
class ProblemFilters(BaseModel):
    """Filters for problem queries."""

    problem_type: ProblemType | None = None
    topic_tags: list[str] | None = None
    target_language_code: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    verb: str | None = None  # Filter by verb infinitive
    metadata_contains: dict[str, Any] | None = None

    # Pagination
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ProblemSearchRequest(BaseModel):
    """Request model for problem search."""

    filters: ProblemFilters = Field(default_factory=ProblemFilters)
    include_statements: bool = Field(
        default=True, description="Whether to include full statements in response"
    )
    include_metadata: bool = Field(
        default=True, description="Whether to include metadata in response"
    )


class ProblemSearchResponse(BaseModel):
    """Response model for problem search."""

    problems: list[Problem | ProblemSummary]
    total_count: int
    has_more: bool
    filters_applied: ProblemFilters
