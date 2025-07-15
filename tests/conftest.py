# tests/conftest.py
"""Shared fixtures for the test suite using local Supabase."""

import pytest
import asyncpg
from typing import Dict, Any
from uuid import uuid4
from faker import Faker
from datetime import datetime, timezone


fake = Faker()


# ===== SUPABASE LOCAL FIXTURES =====


@pytest.fixture
async def supabase_db_connection():
    """Create direct PostgreSQL connection to local Supabase database for db_helpers."""
    # Local Supabase PostgreSQL connection (different from API)
    db_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    connection = await asyncpg.connect(db_url)
    yield connection
    await connection.close()


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
    return client


# ===== TEMPORARILY RESTORED FIXTURES =====
# These will be replaced with supabase-driven fixtures later


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
def sample_api_key():
    """Sample ApiKey model instance for service/mock tests."""
    from src.schemas.api_keys import ApiKey

    return ApiKey(
        id=uuid4(),
        name="Test API Key",
        key_hash="hashed_key_value",
        prefix="sk_live_test",
        permissions=["read", "write"],
        rate_limit=1000,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_used=None,
        usage_count=0,
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
def sample_verb():
    """Simple Verb model instance (alias for sample_db_verb for backward compatibility)."""
    from src.schemas.verbs import Verb, VerbClassification, AuxiliaryType

    return Verb(
        id=uuid4(),
        infinitive="chercher",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        target_language_code="fra",
        translation="to search",
        past_participle="cherché",
        present_participle="cherchant",
        classification=VerbClassification.FIRST_GROUP,
        is_irregular=False,
        can_have_cod=True,
        can_have_coi=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_used=None,
    )


# ===== SCHEMA DATA FIXTURES =====


@pytest.fixture
def sample_verb_data() -> Dict[str, Any]:
    """Sample verb data dictionary for schema tests."""
    return {
        "infinitive": "parler",
        "auxiliary": "avoir",
        "reflexive": False,
        "target_language_code": "eng",
        "translation": "to speak",
        "past_participle": "parlé",
        "present_participle": "parlant",
        "classification": "first_group",
        "is_irregular": False,
        "can_have_cod": True,
        "can_have_coi": False,
    }


@pytest.fixture
def sample_verb_create():
    """Sample VerbCreate instance for schema tests."""
    from src.schemas.verbs import VerbCreate

    return VerbCreate(
        infinitive="parler",
        auxiliary="avoir",
        reflexive=False,
        target_language_code="eng",
        translation="to speak",
        past_participle="parlé",
        present_participle="parlant",
        classification="first_group",
        is_irregular=False,
        can_have_cod=True,
        can_have_coi=False,
    )


@pytest.fixture
def sample_sentence_data() -> Dict[str, Any]:
    """Sample sentence data dictionary for schema tests."""
    return {
        "verb_id": str(uuid4()),
        "subject": "je",
        "tense": "present",
        "correct_conjugation": "parle",
        "text": "Je parle français",
        "translation": "I speak French",
        "is_correct": True,
        "source_language_code": "eng",
        "target_language_code": "fra",
    }


@pytest.fixture
def sample_problem_data() -> Dict[str, Any]:
    """Sample problem data dictionary for schema tests."""
    return {
        "title": "Test Grammar Problem",
        "instructions": "Complete the sentence",
        "problem_type": "grammar",
        "statements": [
            {
                "text": "Je ____ français",
                "translation": "I speak French",
                "explanation": "Uses present tense",
            },
            {
                "text": "Je parlons français",
                "translation": "I speak French",
                "explanation": "Incorrect conjugation",
            },
        ],
        "correct_answer_index": 0,
        "topic_tags": ["present_tense", "regular_verbs"],
        "target_language_code": "fra",
        "source_language_code": "eng",
    }


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


@pytest.fixture
def sample_problem_update():
    """Sample ProblemUpdate instance for testing problem updates."""
    from src.schemas.problems import ProblemUpdate

    return ProblemUpdate(
        title="Updated Test Problem",
        instructions="Updated instructions",
        topic_tags=["updated_tag", "grammar"],
    )
