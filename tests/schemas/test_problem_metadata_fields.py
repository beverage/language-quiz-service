"""Tests for Problem schema with optional metadata fields."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.schemas.problems import Problem, ProblemType


class TestProblemSchemaMetadataFields:
    """Test that Problem schema correctly handles None values for metadata fields."""

    def test_problem_with_none_metadata_fields(self):
        """Problem should accept None for source_statement_ids and metadata."""
        problem_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Test Problem",
            "instructions": "Choose the correct answer",
            "statements": [
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                }
            ],
            "correct_answer_index": 0,
            "target_language_code": "eng",
            "topic_tags": ["test"],
            "source_statement_ids": None,  # Can be None
            "metadata": None,  # Can be None
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        problem = Problem(**problem_data)

        assert problem.source_statement_ids is None
        assert problem.metadata is None

    def test_problem_with_empty_metadata_fields(self):
        """Problem should accept empty list/dict for metadata fields."""
        problem_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Test Problem",
            "instructions": "Choose the correct answer",
            "statements": [
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                }
            ],
            "correct_answer_index": 0,
            "target_language_code": "eng",
            "topic_tags": ["test"],
            "source_statement_ids": [],  # Empty list
            "metadata": {},  # Empty dict
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        problem = Problem(**problem_data)

        assert problem.source_statement_ids == []
        assert problem.metadata == {}

    def test_problem_with_populated_metadata_fields(self):
        """Problem should accept populated metadata fields."""
        statement_ids = [uuid4(), uuid4()]
        metadata = {"verb": "parler", "tense": "present"}

        problem_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Test Problem",
            "instructions": "Choose the correct answer",
            "statements": [
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                }
            ],
            "correct_answer_index": 0,
            "target_language_code": "eng",
            "topic_tags": ["test"],
            "source_statement_ids": statement_ids,
            "metadata": metadata,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        problem = Problem(**problem_data)

        assert problem.source_statement_ids == statement_ids
        assert problem.metadata == metadata

    def test_problem_defaults_to_none_when_omitted(self):
        """Problem should default to None when metadata fields are omitted."""
        problem_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Test Problem",
            "instructions": "Choose the correct answer",
            "statements": [
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                }
            ],
            "correct_answer_index": 0,
            "target_language_code": "eng",
            "topic_tags": ["test"],
            # source_statement_ids omitted
            # metadata omitted
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        problem = Problem(**problem_data)

        # Should default to None (not raise validation error)
        assert problem.source_statement_ids is None
        assert problem.metadata is None

    def test_problem_api_response_compatibility(self):
        """Test that Problem schema matches ProblemResponse output."""
        # Simulate API response with include_metadata=False
        api_response = {
            "id": str(uuid4()),
            "problem_type": "grammar",
            "title": "Test Problem",
            "instructions": "Choose the correct answer",
            "statements": [
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                    "explanation": None,
                }
            ],
            "correct_answer_index": 0,
            "target_language_code": "eng",
            "topic_tags": ["grammar"],
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "source_statement_ids": None,  # API returns None when include_metadata=False
            "metadata": None,
        }

        # This should not raise validation error
        problem = Problem(**api_response)

        assert problem.source_statement_ids is None
        assert problem.metadata is None
