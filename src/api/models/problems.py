"""API models for problem endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.problems import (
    GrammarProblemConstraints,
    ProblemType,
)


class ProblemRandomRequest(BaseModel):
    """Request model for random problem generation."""

    constraints: GrammarProblemConstraints | None = Field(
        None, description="Constraints for problem generation"
    )
    statement_count: int = Field(
        4, ge=2, le=6, description="Number of statements to generate"
    )
    target_language_code: str = Field(
        "eng",
        min_length=3,
        max_length=3,
        description="Target language code for translations (ISO 639-3)",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                # Complete example
                {
                    "constraints": {
                        "grammatical_focus": ["direct_objects", "pronoun_placement"],
                        "verb_infinitives": ["parler", "manger", "finir"],
                        "tenses_used": ["present", "passe_compose"],
                        "includes_negation": True,
                        "includes_cod": True,
                        "includes_coi": False,
                        "difficulty_level": "intermediate",
                    },
                    "statement_count": 4,
                    "target_language_code": "eng",
                },
                # Simple example
                {"statement_count": 6, "target_language_code": "fra"},
                # Empty for random
                {},
            ]
        }
    )


class ProblemStatementResponse(BaseModel):
    """Response model for problem statements."""

    content: str = Field(..., description="Statement content")
    is_correct: bool = Field(..., description="Whether this statement is correct")
    translation: str | None = Field(None, description="Translation of the statement")
    explanation: str | None = Field(
        None, description="Explanation for incorrect statements"
    )


class ProblemResponse(BaseModel):
    """Response model for problems."""

    id: UUID = Field(..., description="Unique problem identifier")
    problem_type: ProblemType = Field(..., description="Type of problem")
    title: str | None = Field(None, description="Problem title")
    instructions: str = Field(..., description="Instructions for solving the problem")
    statements: list[ProblemStatementResponse] = Field(
        ..., description="Problem statements"
    )
    correct_answer_index: int = Field(..., description="Index of the correct answer")
    target_language_code: str = Field(..., description="Target language code")
    topic_tags: list[str] = Field(..., description="Topic tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Optional detailed fields (included when include_metadata=true)
    source_statement_ids: list[UUID] | None = Field(
        None, description="IDs of source sentences used to generate this problem"
    )
    metadata: dict | None = Field(
        None, description="Additional metadata (verb info, grammatical focus, etc.)"
    )

    @classmethod
    def from_problem(cls, problem, include_metadata: bool = False):
        """Create from domain model with optional metadata inclusion."""
        # Convert statements from dict to response models
        statements = []
        for stmt_dict in problem.statements:
            stmt = ProblemStatementResponse(
                content=stmt_dict["content"],
                is_correct=stmt_dict["is_correct"],
                translation=stmt_dict.get("translation"),
                explanation=stmt_dict.get("explanation"),
            )
            statements.append(stmt)

        response_data = {
            "id": problem.id,
            "problem_type": problem.problem_type,
            "title": problem.title,
            "instructions": problem.instructions,
            "statements": statements,
            "correct_answer_index": problem.correct_answer_index,
            "target_language_code": problem.target_language_code,
            "topic_tags": problem.topic_tags,
            "created_at": problem.created_at,
            "updated_at": problem.updated_at,
            # Always include these fields (empty if not requested)
            "source_statement_ids": problem.source_statement_ids
            if include_metadata
            else None,
            "metadata": problem.metadata if include_metadata else None,
        }

        return cls(**response_data)
