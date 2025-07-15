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
async def sample_db_sentence(sentence_repository, verb_repository):
    """Provide a sentence created in the local Supabase database."""
    from tests.verbs.fixtures import generate_random_verb_data
    from src.schemas.verbs import VerbCreate

    # Create a verb first using verb repository
    verb_data = generate_random_verb_data()
    verb_create = VerbCreate(**verb_data)
    verb = await verb_repository.create_verb(verb_create)

    # Create sentence using sentence repository
    sentence_data = generate_random_sentence_data(verb_id=verb.id)
    sentence_create = SentenceCreate(**sentence_data)
    return await sentence_repository.create_sentence(sentence_create)


@pytest.fixture
async def sample_db_sentence_with_known_verb(sentence_repository, verb_repository):
    """Provide a sentence with a known verb for predictable testing."""
    from src.schemas.verbs import VerbCreate, VerbClassification, AuxiliaryType

    # Create a known verb first using verb repository
    known_verb_data = {
        "infinitive": f"parler_{uuid4().hex[:8]}",  # Make unique
        "auxiliary": AuxiliaryType.AVOIR,
        "reflexive": False,
        "target_language_code": "fra",
        "translation": "to speak",
        "past_participle": "parlé",
        "present_participle": "parlant",
        "classification": VerbClassification.FIRST_GROUP,
        "is_irregular": False,
        "can_have_cod": True,
        "can_have_coi": False,
    }
    verb_create = VerbCreate(**known_verb_data)
    verb = await verb_repository.create_verb(verb_create)

    # Create sentence with this verb using sentence repository
    sentence_data = generate_random_sentence_data(
        verb_id=verb.id, target_language_code="eng"
    )
    sentence_create = SentenceCreate(**sentence_data)
    return await sentence_repository.create_sentence(sentence_create)


@pytest.fixture
async def multiple_db_sentences(sentence_repository, verb_repository):
    """Create multiple sentences in the database for testing."""
    from tests.verbs.fixtures import generate_random_verb_data
    from src.schemas.verbs import VerbCreate

    sentences = []
    # Create a shared verb for some sentences using verb repository
    verb_data = generate_random_verb_data()
    verb_create = VerbCreate(**verb_data)
    shared_verb = await verb_repository.create_verb(verb_create)

    for i in range(5):
        if i < 3:
            # First 3 sentences share the same verb
            verb_id = shared_verb.id
        else:
            # Create individual verbs for the last 2 sentences
            individual_verb_data = generate_random_verb_data()
            individual_verb_create = VerbCreate(**individual_verb_data)
            individual_verb = await verb_repository.create_verb(individual_verb_create)
            verb_id = individual_verb.id

        sentence_data = generate_random_sentence_data(
            verb_id=verb_id,
            content=f"Test sentence {i} {fake.word()}",  # Unique content
        )
        sentence_create = SentenceCreate(**sentence_data)
        sentence = await sentence_repository.create_sentence(sentence_create)
        sentences.append(sentence)

    return sentences
