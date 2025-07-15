"""Test fixtures for problem domain."""

import pytest
from faker import Faker
from random import choice, randint
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4, UUID

from src.schemas.problems import ProblemType, ProblemCreate, ProblemUpdate, Problem
from src.repositories.problem_repository import ProblemRepository

fake = Faker()


def generate_random_problem_data(
    problem_type: str = None,
    target_language_code: str = None,
    correct_answer_index: int = None,
    statements: List[Dict[str, Any]] = None,
    topic_tags: List[str] = None,
    title: str = None,
    instructions: str = None,
    source_statement_ids: List[UUID] = None,
    metadata: Dict[str, Any] = None,
) -> Dict[str, Any]:
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

    return {
        "problem_type": problem_type,
        "title": title or fake.sentence(nb_words=4),
        "instructions": instructions or fake.text(max_nb_chars=200),
        "correct_answer_index": correct_answer_index,
        "target_language_code": target_language_code,
        "statements": statements,
        "topic_tags": topic_tags,
        "source_statement_ids": source_statement_ids or [],
        "metadata": metadata or {},
    }


@pytest.fixture
def problem_repository(test_supabase_client):
    """Create ProblemRepository with local Supabase connection."""
    # Return repository using the shared test Supabase client
    return ProblemRepository(client=test_supabase_client)


@pytest.fixture
def sample_problem_data():
    """Provide sample problem data dictionary for testing."""
    return generate_random_problem_data()


@pytest.fixture
def sample_problem_create():
    """Provide a sample ProblemCreate instance for testing."""
    return ProblemCreate(**generate_random_problem_data())


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


@pytest.fixture
def sample_problem_update():
    """Provide a sample ProblemUpdate instance for testing."""
    return ProblemUpdate(
        title=fake.sentence(nb_words=4),
        instructions=fake.text(max_nb_chars=100),
    )


@pytest.fixture
async def sample_db_problem(supabase_db_connection):
    """Provide a problem created in the local Supabase database."""
    from tests.problems.db_helpers import create_problem

    problem_data = generate_random_problem_data()
    return await create_problem(supabase_db_connection, ProblemCreate(**problem_data))


@pytest.fixture
async def multiple_db_problems(supabase_db_connection):
    """Provide multiple problems created in the local Supabase database."""
    from tests.problems.db_helpers import create_problem

    problems = []
    for i in range(3):
        problem_data = generate_random_problem_data(title=f"Test Problem {i+1}")
        problem = await create_problem(
            supabase_db_connection, ProblemCreate(**problem_data)
        )
        problems.append(problem)
    return problems


# Helper functions for cross-domain dependencies


@pytest.fixture
async def sample_verb_for_problems(supabase_db_connection):
    """Create a sample verb for problems that need verbs."""
    from tests.verbs.db_helpers import create_verb
    from tests.verbs.fixtures import generate_random_verb_data

    verb_data = generate_random_verb_data()
    return await create_verb(supabase_db_connection, verb_data)


@pytest.fixture
async def sample_sentence_for_problems(
    supabase_db_connection, sample_verb_for_problems
):
    """Create a sample sentence for problems that need sentences."""
    from tests.sentences.db_helpers import create_sentence
    from tests.sentences.fixtures import generate_random_sentence_data

    sentence_data = generate_random_sentence_data(verb_id=sample_verb_for_problems.id)
    return await create_sentence(supabase_db_connection, **sentence_data)


def _generate_statements_for_type(problem_type: str) -> List[Dict[str, Any]]:
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


def _generate_topic_tags_for_type(problem_type: str) -> List[str]:
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
