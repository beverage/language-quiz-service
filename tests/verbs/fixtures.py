"""
Fixtures and test data generators for verb repository tests.
Keeps conftest.py clean by separating domain-specific test utilities.
"""

from datetime import UTC, datetime
from random import choice
from typing import Any
from uuid import uuid4

import pytest
from faker import Faker

from src.repositories.verb_repository import VerbRepository
from src.schemas.verbs import (
    AuxiliaryType,
    Tense,
    Verb,
    VerbClassification,
    VerbCreate,
)
from src.services.verb_service import VerbService

fake = Faker()


@pytest.fixture
async def verb_service(test_supabase_client, mock_llm_client, redis_client):
    """Create a VerbService with real repository connection, caches, and mock LLM client."""
    from src.cache.conjugation_cache import ConjugationCache
    from src.cache.verb_cache import VerbCache

    verb_repository = VerbRepository(client=test_supabase_client)

    # Get the unique namespace for this test
    namespace = redis_client._test_namespace

    # Create caches with Redis client and namespace for isolation
    verb_cache = VerbCache(redis_client, namespace=namespace)
    conjugation_cache = ConjugationCache(redis_client, namespace=namespace)

    # Load caches from database
    await verb_cache.load(verb_repository)
    await conjugation_cache.load(verb_repository)

    return VerbService(
        llm_client=mock_llm_client,
        verb_repository=verb_repository,
        verb_cache=verb_cache,
        conjugation_cache=conjugation_cache,
    )


def generate_random_verb_data() -> dict[str, Any]:
    """Generate random verb data for testing.

    All test-generated verbs are marked with is_test=True to exclude
    them from random selection during problem generation.
    """
    infinitive = f"{fake.word()}_{uuid4().hex[:8]}"  # Make unique

    return {
        "infinitive": infinitive,
        "auxiliary": choice(["avoir", "être"]),
        "reflexive": choice([True, False]),
        "target_language_code": choice(["fra", "eng", "esp"]),
        "translation": fake.word(),
        "past_participle": f"{infinitive[:-2]}é"
        if infinitive.endswith(("er", "ir"))
        else fake.word(),
        "present_participle": f"{infinitive[:-2]}ant"
        if infinitive.endswith(("er", "ir"))
        else fake.word(),
        "classification": choice([cls.value for cls in VerbClassification]),
        "is_irregular": choice([True, False]),
        "can_have_cod": choice([True, False]),
        "can_have_coi": choice([True, False]),
        "is_test": True,
    }


def generate_sample_verb_data(infinitive: str | None = None) -> dict[str, Any]:
    """Generate sample verb data dictionary for testing (callable function)."""
    data = generate_random_verb_data()
    if infinitive:
        data["infinitive"] = infinitive
    return data


@pytest.fixture
def sample_verb_data() -> dict[str, Any]:
    """Provide sample verb data dictionary for testing (fixture)."""
    return generate_random_verb_data()


def generate_random_conjugation_data() -> dict[str, Any]:
    """Generate random conjugation data for testing."""
    infinitive = f"{fake.word()}_{uuid4().hex[:8]}"  # Make unique
    return {
        "infinitive": infinitive,
        "auxiliary": choice(["avoir", "être"]),
        "reflexive": choice([True, False]),
        "tense": choice([tense.value for tense in Tense]),
        "first_person_singular": fake.word(),
        "second_person_singular": fake.word(),
        "third_person_singular": fake.word(),
        "first_person_plural": fake.word(),
        "second_person_plural": fake.word(),
        "third_person_plural": fake.word(),
    }


@pytest.fixture
def sample_verb_create() -> VerbCreate:
    """Provide a sample VerbCreate instance for testing."""
    return VerbCreate(**generate_random_verb_data())


@pytest.fixture
def sample_verb():
    """Note to agents - do not use this fixture!!!  It returns fixed data unsuitable for testing."""
    return Verb(
        id=uuid4(),
        infinitive="parler",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        target_language_code="fra",
        translation="to speak",
        past_participle="parlé",
        present_participle="parlant",
        classification=VerbClassification.FIRST_GROUP,
        is_irregular=False,
        can_have_cod=True,
        can_have_coi=False,
        is_test=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        last_used_at=None,
        usage_count=0,
    )


@pytest.fixture
def verb_repository(test_supabase_client):
    """Create a VerbRepository instance for testing with testcontainers."""
    # Return repository using the shared test Supabase client
    return VerbRepository(client=test_supabase_client)
