"""Test fixtures for sentence repository tests."""

import pytest
from typing import Dict, Any
from random import choice
from uuid import uuid4, UUID
from faker import Faker

from src.schemas.sentences import (
    SentenceCreate,
    SentenceUpdate,
    Pronoun,
    Tense,
    DirectObject,
    IndirectObject,
    Negation,
)
from src.repositories.sentence_repository import SentenceRepository

fake = Faker()


def generate_random_sentence_data(
    verb_id: UUID = None, target_language_code: str = None, **overrides
) -> Dict[str, Any]:
    """Generate random sentence data for testing."""
    if verb_id is None:
        verb_id = uuid4()
    if target_language_code is None:
        target_language_code = choice(["eng", "fra", "esp"])

    base_data = {
        "content": fake.sentence(),
        "translation": fake.sentence(),
        "verb_id": verb_id,
        "pronoun": choice([p.value for p in Pronoun]),
        "tense": choice([t.value for t in Tense]),
        "direct_object": choice([d.value for d in DirectObject]),
        "indirect_object": choice([i.value for i in IndirectObject]),
        "negation": choice([n.value for n in Negation]),
        "is_correct": choice([True, False]),
        "explanation": fake.text() if choice([True, False]) else None,
        "source": fake.word() if choice([True, False]) else None,
        "target_language_code": target_language_code,
    }

    # Apply any overrides
    base_data.update(overrides)
    return base_data


@pytest.fixture
def sentence_repository(test_supabase_client):
    """Create a SentenceRepository instance for testing with testcontainers."""
    # Return repository using the shared test Supabase client
    return SentenceRepository(client=test_supabase_client)


@pytest.fixture
def sample_sentence_data() -> Dict[str, Any]:
    """Provide sample sentence data dictionary for testing."""
    return generate_random_sentence_data()


@pytest.fixture
def sample_sentence_create() -> SentenceCreate:
    """Provide a sample SentenceCreate instance for testing."""
    return SentenceCreate(**generate_random_sentence_data())


@pytest.fixture
def sample_sentence_update() -> SentenceUpdate:
    """Provide a sample SentenceUpdate instance for testing."""
    return SentenceUpdate(
        content=fake.sentence(),
        translation=fake.sentence(),
        is_correct=choice([True, False]),
    )


@pytest.fixture
def sample_sentence_with_custom_data():
    """Provide a SentenceCreate with specific test data."""
    return SentenceCreate(
        content=fake.sentence(),
        translation=fake.sentence(),
        is_correct=choice([True, False]),
    )


@pytest.fixture
async def sample_db_sentence(supabase_db_connection):
    """Provide a sentence created in the local Supabase database."""
    from tests.sentences.db_helpers import create_sentence

    sentence_data = generate_random_sentence_data()
    return await create_sentence(supabase_db_connection, **sentence_data)


@pytest.fixture
async def sample_db_sentence_with_known_verb(supabase_db_connection):
    """Provide a sentence with a known verb for predictable testing."""
    from tests.verbs.db_helpers import create_verb
    from tests.sentences.db_helpers import create_sentence

    # Create a known verb first
    verb = await create_verb(
        supabase_db_connection, infinitive="parler", target_language_code="fra"
    )

    # Create sentence with this verb
    return await create_sentence(
        supabase_db_connection, verb_id=verb.id, target_language_code="eng"
    )


@pytest.fixture
async def multiple_db_sentences(supabase_db_connection):
    """Create multiple sentences in the database for testing."""
    from tests.verbs.db_helpers import create_verb
    from tests.sentences.db_helpers import create_sentence

    sentences = []
    # Create a shared verb for some sentences
    verb = await create_verb(supabase_db_connection)

    for i in range(5):
        sentence = await create_sentence(
            supabase_db_connection,
            verb_id=verb.id if i < 3 else None,  # First 3 share a verb
            content=f"Test sentence {i} {fake.word()}",  # Unique content
        )
        sentences.append(sentence)
    return sentences
