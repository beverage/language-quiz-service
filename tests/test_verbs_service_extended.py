"""Extended unit tests for the Verb Service to improve coverage."""

import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from src.services.verb_service import VerbService
from src.schemas.verbs import Verb, VerbCreate
from uuid import uuid4
from datetime import datetime, timezone


@pytest.fixture
def mock_verb_repo():
    """Fixture for a mocked VerbRepository."""
    repo = AsyncMock()
    repo.upsert_verb = AsyncMock()
    repo.upsert_conjugation = AsyncMock()
    repo.get_verb_with_conjugations_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_ai_client():
    """Fixture for a mocked OpenAIClient."""
    return AsyncMock()


@pytest.fixture
def mock_prompt_generator():
    """Fixture for a mocked VerbPromptGenerator."""
    return MagicMock()


@pytest.fixture
def verb_service(monkeypatch, mock_ai_client, mock_verb_repo, mock_prompt_generator):
    """Fixture for VerbService with mocked dependencies."""
    service = VerbService()
    monkeypatch.setattr(service, "openai_client", mock_ai_client)
    monkeypatch.setattr(service, "verb_repository", mock_verb_repo)
    monkeypatch.setattr(service, "verb_prompt_generator", mock_prompt_generator)
    return service


@pytest.mark.asyncio
async def test_download_verb_success(verb_service, mock_ai_client, mock_verb_repo):
    """Test successful verb download and processing from AI."""
    verb_infinitive = "parler"
    mock_ai_response = {
        "infinitive": "parler",
        "auxiliary": "avoir",
        "reflexive": False,
        "target_language_code": "eng",
        "translation": "to speak",
        "past_participle": "parlé",
        "present_participle": "parlant",
        "classification": "first_group",
        "is_irregular": False,
        "tenses": [
            {
                "infinitive": "parler",
                "auxiliary": "avoir",
                "reflexive": False,
                "tense": "present",
                "first_person_singular": "parle",
                "second_person_singular": "parles",
                "third_person_singular": "parle",
                "first_person_plural": "parlons",
                "second_person_formal": "parlez",
                "third_person_plural": "parlent",
            }
        ],
    }
    mock_ai_client.handle_request.return_value = json.dumps(mock_ai_response)

    verb_create_data = VerbCreate.model_validate(mock_ai_response).model_dump()
    mock_verb = Verb(
        id=uuid4(),
        **verb_create_data,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_verb_repo.upsert_verb.return_value = mock_verb
    mock_verb_repo.get_verb_with_conjugations_by_id.return_value = (
        mock_verb  # Simplified for test
    )

    result = await verb_service.download_verb(verb_infinitive)

    mock_ai_client.handle_request.assert_awaited_once()
    mock_verb_repo.upsert_verb.assert_awaited_once()
    mock_verb_repo.upsert_conjugation.assert_awaited_once()
    assert result == mock_verb


@pytest.mark.asyncio
async def test_download_verb_invalid_json(verb_service, mock_ai_client):
    """Test verb download with invalid JSON from AI."""
    verb_infinitive = "chanter"
    mock_ai_client.handle_request.return_value = "this is not json"

    with pytest.raises(ValueError, match="Invalid response format from the LLM"):
        await verb_service.download_verb(verb_infinitive)


@pytest.mark.asyncio
async def test_download_verb_validation_error(verb_service, mock_ai_client):
    """Test verb download with data that fails Pydantic validation."""
    verb_infinitive = "manger"
    mock_ai_response = {
        "infinitive": "manger",
        # Missing required 'auxiliary' field
    }
    mock_ai_client.handle_request.return_value = json.dumps(mock_ai_response)

    with pytest.raises(ValueError, match="Invalid response format from the LLM"):
        await verb_service.download_verb(verb_infinitive)


@pytest.mark.asyncio
async def test_download_verb_empty_response(verb_service, mock_ai_client):
    """Test verb download with an empty response from AI."""
    verb_infinitive = "danser"
    mock_ai_client.handle_request.return_value = ""

    with pytest.raises(ValueError, match="Invalid response format from the LLM"):
        await verb_service.download_verb(verb_infinitive)
