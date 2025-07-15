# tests/conftest.py
"""Shared fixtures for the test suite using local Supabase."""

import pytest
from typing import Dict, Any
from uuid import uuid4
from faker import Faker
from datetime import datetime, timezone


fake = Faker()


# ===== SUPABASE LOCAL FIXTURES =====


@pytest.fixture
async def test_supabase_client():
    """Create a Supabase client for testing that points to local Supabase instance."""
    import json
    import subprocess
    from src.clients.supabase import create_test_supabase_client

    # Local Supabase API connection details
    supabase_url = "http://127.0.0.1:54321"

    # Get service role key from supabase status
    try:
        result = subprocess.run(
            ["supabase", "status", "--output", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        status_data = json.loads(result.stdout)
        service_role_key = status_data.get("SERVICE_ROLE_KEY", "")

        if not service_role_key:
            raise ValueError("SERVICE_ROLE_KEY not found in supabase status output")

    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Failed to get service role key from supabase status: {e}")

    # Create and return Supabase client for local instance
    client = await create_test_supabase_client(supabase_url, service_role_key)
    yield client
    # No explicit cleanup needed - client connections are handled automatically


# ===== SERVICE/MOCK TEST FIXTURES =====


@pytest.fixture
def sample_db_verb():
    """Sample Verb model instance for service/mock tests."""
    from src.schemas.verbs import Verb, VerbClassification, AuxiliaryType

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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_used=None,
    )


@pytest.fixture
def sample_problem():
    """Sample Problem model instance for service/mock tests."""
    from src.schemas.problems import Problem, ProblemType, StatementModel

    return Problem(
        id=uuid4(),
        title="Test Grammar Problem",
        instructions="Complete the sentence",
        problem_type=ProblemType.GRAMMAR,
        statements=[
            StatementModel(
                text="Je ____ français",
                translation="I speak French",
                explanation="Uses present tense",
            ),
            StatementModel(
                text="Je parlons français",
                translation="I speak French",
                explanation="Incorrect conjugation",
            ),
        ],
        correct_answer_index=0,
        topic_tags=["present_tense", "regular_verbs"],
        target_language_code="fra",
        source_language_code="eng",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        difficulty_score=0.5,
        is_active=True,
    )


@pytest.fixture
def sample_db_conjugation():
    """Sample Conjugation model instance for service/mock tests."""
    from src.schemas.verbs import Conjugation, Tense, AuxiliaryType

    return Conjugation(
        id=uuid4(),
        verb_id=uuid4(),
        infinitive="parler",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        tense=Tense.PRESENT,
        first_person_singular="parle",
        second_person_singular="parles",
        third_person_singular="parle",
        first_person_plural="parlons",
        second_person_plural="parlez",
        third_person_plural="parlent",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_db_sentence():
    """Sample Sentence model instance for service/mock tests."""
    from src.schemas.sentences import (
        Sentence,
        Tense,
        Pronoun,
        DirectObject,
        IndirectObject,
        Negation,
    )

    return Sentence(
        id=uuid4(),
        verb_id=uuid4(),
        target_language_code="fra",
        content="Je parle français",
        translation="I speak French",
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.NONE,
        indirect_object=IndirectObject.NONE,
        negation=Negation.NONE,
        is_correct=True,
        explanation=None,
        source=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_conjugation_create():
    """Sample ConjugationCreate instance for service/mock tests."""
    from src.schemas.verbs import ConjugationCreate, AuxiliaryType

    return ConjugationCreate(
        verb_id=uuid4(),
        target_language_code="fra",
        infinitive="parler",
        auxiliary=AuxiliaryType.AVOIR,
        tense="present",
        first_person_singular="parle",
        second_person_singular="parles",
        third_person_singular="parle",
        first_person_plural="parlons",
        second_person_plural="parlez",
        third_person_plural="parlent",
    )
