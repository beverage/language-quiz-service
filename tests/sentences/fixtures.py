"""Test fixtures for sentence repository tests."""

from random import choice
from typing import Any
from uuid import UUID, uuid4

import pytest
from faker import Faker

from src.repositories.sentence_repository import SentenceRepository
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    Tense,
)

fake = Faker()


def generate_random_sentence_data(
    verb_id: UUID = None, target_language_code: str = None, **overrides
) -> dict[str, Any]:
    """Generate random sentence data for testing.

    Note: ANY values are excluded as they are generation-only concepts
    and cannot be stored in the database.
    """
    if verb_id is None:
        verb_id = uuid4()
    if target_language_code is None:
        target_language_code = choice(["eng", "fra", "esp"])

    # Exclude ANY values - they are for generation only, not storage
    storable_direct_objects = [d.value for d in DirectObject if d != DirectObject.ANY]
    storable_indirect_objects = [
        i.value for i in IndirectObject if i != IndirectObject.ANY
    ]
    storable_negations = [n.value for n in Negation if n != Negation.ANY]

    base_data = {
        "content": fake.sentence(),
        "translation": fake.sentence(),
        "verb_id": verb_id,
        "pronoun": choice([p.value for p in Pronoun]),
        "tense": choice([t.value for t in Tense]),
        "direct_object": choice(storable_direct_objects),
        "indirect_object": choice(storable_indirect_objects),
        "negation": choice(storable_negations),
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
