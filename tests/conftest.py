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
)
from unittest.mock import MagicMock, AsyncMock
from src.repositories.verb_repository import VerbRepository
from src.clients.openai_client import OpenAIClient


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
def sample_verb(sample_verb_data: dict) -> VerbCreate:
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
def mock_supabase_client() -> MagicMock:
    """Provides a mock Supabase client for testing."""
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute = AsyncMock()
    mock_client.table.return_value.select.return_value.eq.return_value.execute = (
        AsyncMock()
    )
    mock_client.table.return_value.select.return_value.limit.return_value.execute = (
        AsyncMock()
    )
    mock_client.table.return_value.update.return_value.eq.return_value.execute = (
        AsyncMock()
    )
    mock_client.table.return_value.delete.return_value.eq.return_value.execute = (
        AsyncMock()
    )
    mock_client.rpc.return_value.execute = AsyncMock()
    return mock_client


@pytest.fixture
def mock_verb_repository() -> MagicMock:
    """Provides a mock VerbRepository for service tests."""
    mock = MagicMock(spec=VerbRepository)
    mock.create_verb = AsyncMock()
    mock.get_verb = AsyncMock()
    mock.update_verb = AsyncMock()
    mock.delete_verb = AsyncMock()
    mock.get_verb_by_infinitive = AsyncMock()
    mock.get_verbs_by_infinitive = AsyncMock()
    mock.get_all_verbs = AsyncMock()
    mock.get_random_verb = AsyncMock()
    mock.update_last_used = AsyncMock()
    mock.delete_conjugations_by_verb = AsyncMock()
    mock.get_verb_with_conjugations = AsyncMock()
    return mock


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Provides a mock OpenAIClient for testing."""
    mock = MagicMock(spec=OpenAIClient)
    mock.handle_request = AsyncMock()
    return mock
