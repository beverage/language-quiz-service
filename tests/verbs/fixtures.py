"""
Fixtures and test data generators for verb repository tests.
Keeps conftest.py clean by separating domain-specific test utilities.
"""

import pytest
from typing import Dict, Any
from random import choice
from faker import Faker
from uuid import uuid4

from src.schemas.verbs import (
    VerbCreate,
    VerbUpdate,
    VerbClassification,
    Tense,
)
from src.repositories.verb_repository import VerbRepository


fake = Faker()


def generate_random_verb_data() -> Dict[str, Any]:
    """Generate random verb data for testing."""
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
    }


def generate_random_conjugation_data() -> Dict[str, Any]:
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
def sample_verb_data() -> Dict[str, Any]:
    """Provide sample verb data dictionary for testing."""
    return generate_random_verb_data()


@pytest.fixture
def sample_verb_create() -> VerbCreate:
    """Provide a sample VerbCreate instance for testing."""
    return VerbCreate(**generate_random_verb_data())


@pytest.fixture
def sample_verb_update() -> VerbUpdate:
    """Provide a sample VerbUpdate instance for testing."""
    return VerbUpdate(translation=fake.word())


@pytest.fixture
def sample_conjugation_data() -> Dict[str, Any]:
    """Provide sample conjugation data dictionary for testing."""
    return generate_random_conjugation_data()


# ============================================================================
# Domain-specific test data patterns
# ============================================================================


def generate_specific_verb_data(infinitive: str, **overrides) -> Dict[str, Any]:
    """Generate verb data with specific infinitive for predictable tests."""
    base_data = generate_random_verb_data()
    base_data["infinitive"] = infinitive
    base_data.update(overrides)
    return base_data


def generate_specific_conjugation_data(
    infinitive: str, tense: str, **overrides
) -> Dict[str, Any]:
    """Generate conjugation data with specific infinitive and tense."""
    base_data = generate_random_conjugation_data()
    base_data["infinitive"] = infinitive
    base_data["tense"] = tense
    base_data.update(overrides)
    return base_data


# ============================================================================
# Complex domain data for testing edge cases
# ============================================================================


def generate_standard_french_verb_set() -> Dict[str, Any]:
    """Generate a standard French verb like 'parler' for consistent testing."""
    unique_suffix = uuid4().hex[:8]
    infinitive = f"parler_{unique_suffix}"

    return {
        "infinitive": infinitive,
        "auxiliary": "avoir",
        "reflexive": False,
        "target_language_code": "fra",
        "translation": "to speak",
        "past_participle": f"parlé_{unique_suffix}",
        "present_participle": f"parlant_{unique_suffix}",
        "classification": "regular",
        "is_irregular": False,
        "can_have_cod": True,
        "can_have_coi": False,
        "present_conjugations": {
            "first_person_singular": "parle",
            "second_person_singular": "parles",
            "third_person_singular": "parle",
            "first_person_plural": "parlons",
            "second_person_formal": "parlez",
            "third_person_plural": "parlent",
        },
    }


@pytest.fixture
def verb_repository(test_supabase_client):
    """Create a VerbRepository instance for testing with testcontainers."""
    # Return repository using the shared test Supabase client
    return VerbRepository(client=test_supabase_client)
