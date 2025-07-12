"""Unit tests for the Verb Service."""

from unittest.mock import MagicMock

import pytest
from src.repositories.verb_repository import VerbRepository
from src.services.verb_service import VerbService
from src.schemas.verbs import Verb, VerbCreate, VerbUpdate
from src.clients.openai_client import OpenAIClient
from src.prompts.verb_prompts import VerbPromptGenerator
import json


@pytest.fixture
def mock_verb_repository():
    """Fixture for a mocked VerbRepository."""
    return MagicMock(spec=VerbRepository)


@pytest.fixture
def mock_openai_client():
    """Fixture for a mocked OpenAIClient."""
    return MagicMock(spec=OpenAIClient)


@pytest.fixture
def mock_verb_prompt_generator():
    """Fixture for a mocked VerbPromptGenerator."""
    return MagicMock(spec=VerbPromptGenerator)


@pytest.fixture
def verb_service(
    monkeypatch,
    mock_verb_repository: MagicMock,
    mock_openai_client: MagicMock,
    mock_verb_prompt_generator: MagicMock,
) -> VerbService:
    """Fixture for a VerbService with mocked dependencies."""
    service = VerbService()
    monkeypatch.setattr(service, "openai_client", mock_openai_client)
    monkeypatch.setattr(service, "verb_prompt_generator", mock_verb_prompt_generator)
    monkeypatch.setattr(service, "verb_repository", mock_verb_repository)
    return service


@pytest.mark.unit
class TestVerbService:
    """Test suite for the VerbService."""

    async def test_create_verb(
        self,
        verb_service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Test creating a verb."""
        mock_verb_repository.create_verb.return_value = sample_db_verb
        verb_create = VerbCreate(**sample_db_verb.model_dump())

        created_verb = await verb_service.create_verb(verb_create)

        assert created_verb == sample_db_verb
        mock_verb_repository.create_verb.assert_awaited_once_with(verb_create)

    async def test_get_verb(
        self,
        verb_service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Test getting a verb by ID."""
        mock_verb_repository.get_verb.return_value = sample_db_verb
        verb_id = sample_db_verb.id

        verb = await verb_service.get_verb(verb_id)

        assert verb == sample_db_verb
        mock_verb_repository.get_verb.assert_awaited_once_with(verb_id)

    async def test_get_random_verb(
        self,
        verb_service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Test getting a random verb."""
        mock_verb_repository.get_random_verb.return_value = sample_db_verb
        verb_id = sample_db_verb.id

        verb = await verb_service.get_random_verb()

        assert verb == sample_db_verb
        mock_verb_repository.get_random_verb.assert_awaited_once()
        mock_verb_repository.update_last_used.assert_awaited_once_with(verb_id)

    async def test_update_verb(
        self,
        verb_service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Test updating a verb."""
        updated_verb = sample_db_verb.model_copy(
            update={"infinitive": "new infinitive"}
        )
        mock_verb_repository.update_verb.return_value = updated_verb
        verb_id = sample_db_verb.id
        update_data = VerbUpdate(infinitive="new infinitive")

        verb = await verb_service.update_verb(verb_id, update_data)

        assert verb == updated_verb
        mock_verb_repository.update_verb.assert_awaited_once_with(verb_id, update_data)

    async def test_delete_verb(
        self,
        verb_service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Test deleting a verb."""
        mock_verb_repository.get_verb.return_value = sample_db_verb
        mock_verb_repository.delete_verb.return_value = True
        verb_id = sample_db_verb.id

        result = await verb_service.delete_verb(verb_id)

        assert result is True
        mock_verb_repository.get_verb.assert_awaited_once_with(verb_id)
        mock_verb_repository.delete_conjugations_by_verb.assert_awaited_once_with(
            infinitive=sample_db_verb.infinitive,
            auxiliary=sample_db_verb.auxiliary.value,
            reflexive=sample_db_verb.reflexive,
        )
        mock_verb_repository.delete_verb.assert_awaited_once_with(verb_id)

    async def test_download_verb_ai_integration(
        self,
        verb_service: VerbService,
        mock_openai_client: MagicMock,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests the AI-powered verb downloading feature."""
        verb_infinitive = "parler"
        ai_response = {
            **sample_db_verb.model_dump(exclude={"id", "created_at", "updated_at"}),
            "tenses": [],
        }
        mock_openai_client.handle_request.return_value = json.dumps(
            ai_response, default=str
        )

        # Simulate that the verb does not exist yet
        mock_verb_repository.get_verb_by_infinitive.return_value = None
        # Simulate verb creation
        mock_verb_repository.upsert_verb.return_value = sample_db_verb

        verb = await verb_service.download_verb(verb_infinitive)

        assert verb == sample_db_verb
        mock_openai_client.handle_request.assert_awaited_once()
        mock_verb_repository.upsert_verb.assert_awaited_once()

    async def test_download_verb_invalid_ai_response(
        self, verb_service: VerbService, mock_openai_client: MagicMock
    ):
        """Tests handling of invalid JSON from the AI client."""
        mock_openai_client.handle_request.return_value = "invalid json"

        with pytest.raises(ValueError, match="Invalid response format from the LLM"):
            await verb_service.download_verb("parler")

    async def test_get_verb_with_conjugations(
        self,
        verb_service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Test getting a verb with its conjugations."""
        mock_verb_repository.get_verbs_by_infinitive.return_value = [sample_db_verb]
        mock_verb_repository.get_verb_with_conjugations.return_value = sample_db_verb

        verb_with_conjugations = await verb_service.get_verb_with_conjugations(
            sample_db_verb.infinitive
        )

        assert verb_with_conjugations == sample_db_verb
        mock_verb_repository.get_verb_with_conjugations.assert_awaited_once_with(
            infinitive=sample_db_verb.infinitive,
            auxiliary=sample_db_verb.auxiliary.value,
            reflexive=sample_db_verb.reflexive,
            target_language_code="eng",
        )
