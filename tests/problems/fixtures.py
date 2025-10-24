"""Test fixtures for problem domain."""

from datetime import datetime
from random import choice, randint
from typing import Any
from uuid import uuid4

import pytest
from faker import Faker

from src.repositories.problem_repository import ProblemRepository
from src.schemas.problems import Problem, ProblemType

fake = Faker()


@pytest.fixture
async def mock_llm_responses():
    """Mock LLM responses for consistent testing."""
    import itertools

    # Mock sentence generation responses - enough variety for testing
    sentence_responses = [
        '{"sentence": "Je parle français.", "translation": "I speak French.", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
        '{"sentence": "Je parles français.", "translation": "", "is_correct": false, "explanation": "Wrong conjugation", "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
        '{"sentence": "Je ne parle pas français.", "translation": "I do not speak French.", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "pas"}',
        '{"sentence": "Je parle le français.", "translation": "I speak the French.", "is_correct": false, "explanation": "Incorrect article usage", "has_compliment_object_direct": true, "has_compliment_object_indirect": false, "direct_object": "masculine", "indirect_object": "none", "negation": "none"}',
        '{"sentence": "Tu parles bien.", "translation": "You speak well.", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
        '{"sentence": "Il parle mal.", "translation": "He speaks badly.", "is_correct": false, "explanation": "Poor grammar", "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "direct_object": "none", "indirect_object": "none", "negation": "none"}',
    ]
    # Return infinite cycle of responses to handle multiple LLM calls per test
    return itertools.cycle(sentence_responses)


def generate_random_problem_data(
    problem_type: str = None,
    target_language_code: str = None,
    correct_answer_index: int = None,
    statements: list[dict[str, Any]] = None,
    topic_tags: list[str] = None,
    title: str = None,
    instructions: str = None,
    metadata: dict[str, Any] = None,
) -> dict[str, Any]:
    """Generate random problem data for testing."""
    if problem_type is None:
        # Only use GRAMMAR type since FUNCTIONAL and VOCABULARY are not implemented yet
        problem_type = ProblemType.GRAMMAR.value

    if target_language_code is None:
        target_language_code = choice(["eng", "fra", "esp"])

    if statements is None:
        statements = _generate_statements_for_type(problem_type)

    # Ensure correct_answer_index is valid
    if correct_answer_index is None:
        correct_answer_index = randint(0, len(statements) - 1)

    # Generate topic tags based on problem type
    if topic_tags is None:
        topic_tags = _generate_topic_tags_for_type(problem_type)

    # Ensure test_data tag is always present
    if "test_data" not in topic_tags:
        topic_tags = ["test_data"] + topic_tags

    return {
        "problem_type": problem_type,
        "title": title or fake.sentence(nb_words=4),
        "instructions": instructions or fake.text(max_nb_chars=200),
        "correct_answer_index": correct_answer_index,
        "target_language_code": target_language_code,
        "statements": statements,
        "topic_tags": topic_tags,
        "source_statement_ids": [],
        "metadata": metadata or {},
    }


@pytest.fixture
async def problem_repository(test_supabase_client):
    """Create a ProblemRepository instance with Supabase client for testing."""
    return ProblemRepository(test_supabase_client)


@pytest.fixture
def sample_problem_data():
    """Provide sample problem data dictionary for testing."""
    return generate_random_problem_data()


@pytest.fixture
def sample_problem():
    """Provide a sample Problem instance for testing."""
    problem_data = generate_random_problem_data()
    problem_data.update(
        {
            "id": uuid4(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    )
    return Problem(**problem_data)


def _generate_statements_for_type(problem_type: str) -> list[dict[str, Any]]:
    """Generate statements based on problem type."""
    if problem_type == ProblemType.GRAMMAR.value:
        return [
            {
                "content": "Je mange une pomme",
                "is_correct": True,
                "translation": "I eat an apple",
            },
            {
                "content": "Je manges une pomme",
                "is_correct": False,
                "explanation": "Incorrect verb conjugation - should be 'mange' not 'manges' with 'je'",
            },
            {
                "content": "Je mange un pomme",
                "is_correct": False,
                "explanation": "Incorrect article - 'pomme' is feminine, should use 'une' not 'un'",
            },
            {
                "content": "J'mange une pomme",
                "is_correct": False,
                "explanation": "Missing proper contraction - should be 'Je mange' not 'J'mange'",
            },
        ]
    else:
        # Only GRAMMAR type is supported
        raise ValueError(
            f"Unsupported problem type: {problem_type}. Only GRAMMAR is currently supported."
        )


def _generate_topic_tags_for_type(problem_type: str) -> list[str]:
    """Generate appropriate topic tags based on problem type."""
    if problem_type == ProblemType.GRAMMAR.value:
        return choice(
            [
                ["grammar", "articles"],
                ["grammar", "conjugation"],
                ["grammar", "tenses"],
                ["grammar", "pronouns"],
            ]
        )
    else:
        # Only GRAMMAR type is supported
        raise ValueError(
            f"Unsupported problem type: {problem_type}. Only GRAMMAR is currently supported."
        )
