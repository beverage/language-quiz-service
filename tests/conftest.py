# tests/conftest.py
"""Shared fixtures for the test suite."""

import pytest

from datetime import datetime, timezone
from uuid import uuid4

from src.schemas.verbs import (
    AuxiliaryType,
    VerbClassification,
    VerbCreate,
    Verb,
    ConjugationCreate,
    Conjugation,
)
from src.schemas.sentences import (
    Sentence,
    SentenceCreate,
    Pronoun,
    Tense,
    DirectObject,
    IndirectObject,
    Negation,
)


# Environment variables are now handled via default values in Settings class


@pytest.fixture
def sample_verb_data() -> dict:
    """Provides a dictionary of valid verb data for testing."""
    return {
        "infinitive": "parler",
        "auxiliary": AuxiliaryType.AVOIR,
        "reflexive": False,
        "target_language_code": "eng",
        "translation": "to speak",
        "past_participle": "parlé",
        "present_participle": "parlant",
        "classification": VerbClassification.FIRST_GROUP,
        "is_irregular": False,
    }


@pytest.fixture
def sample_irregular_verb_data() -> dict:
    """Provides a dictionary of valid irregular verb data for testing."""
    return {
        "infinitive": "être",
        "auxiliary": AuxiliaryType.ETRE,
        "reflexive": False,
        "target_language_code": "eng",
        "translation": "to be",
        "past_participle": "été",
        "present_participle": "étant",
        "classification": VerbClassification.THIRD_GROUP,
        "is_irregular": True,
    }


@pytest.fixture
def sample_verb_create(sample_verb_data: dict) -> VerbCreate:
    """Provides a valid VerbCreate instance for testing."""
    return VerbCreate(**sample_verb_data)


@pytest.fixture
def sample_irregular_verb(sample_irregular_verb_data: dict) -> VerbCreate:
    """Provides a valid irregular VerbCreate instance for testing."""
    return VerbCreate(**sample_irregular_verb_data)


@pytest.fixture
def sample_db_verb(sample_verb_data: dict) -> Verb:
    """Provides a valid Verb instance as if it were from the database."""
    return Verb(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **sample_verb_data,
    )


@pytest.fixture
def sample_conjugation_create(sample_db_verb: Verb) -> ConjugationCreate:
    """Provides a valid ConjugationCreate instance for testing."""
    return ConjugationCreate(
        infinitive=sample_db_verb.infinitive,
        auxiliary=sample_db_verb.auxiliary,
        reflexive=sample_db_verb.reflexive,
        tense=Tense.PRESENT,
        first_person_singular="parle",
        second_person_singular="parles",
        third_person_singular="parle",
        first_person_plural="parlons",
        second_person_formal="parlez",
        third_person_plural="parlent",
    )


@pytest.fixture
def sample_db_conjugation(sample_conjugation_create: ConjugationCreate) -> Conjugation:
    """Provides a valid Conjugation instance as if from the database."""
    return Conjugation(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **sample_conjugation_create.model_dump(),
    )


@pytest.fixture
def sample_sentence_data(sample_db_verb: Verb) -> dict:
    """Provides a dictionary of valid sentence data for testing."""
    return {
        "target_language_code": "eng",
        "content": "Je parle.",
        "translation": "I am speaking.",
        "verb_id": sample_db_verb.id,
        "pronoun": Pronoun.FIRST_PERSON,
        "tense": Tense.PRESENT,
        "direct_object": DirectObject.NONE,
        "indirect_object": IndirectObject.NONE,
        "negation": Negation.NONE,
        "is_correct": True,
    }


@pytest.fixture
def sample_sentence(sample_sentence_data: dict) -> SentenceCreate:
    """Provides a valid SentenceCreate instance for testing."""
    return SentenceCreate(**sample_sentence_data)


@pytest.fixture
def sample_db_sentence(sample_sentence_data: dict) -> Sentence:
    """Provides a valid Sentence instance as if from the database."""
    return Sentence(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **sample_sentence_data,
    )
