"""Test fixtures for sentence repository tests."""

import pytest
from typing import Dict, Any
from random import choice
from uuid import uuid4, UUID
from faker import Faker

from src.schemas.sentences import (
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
