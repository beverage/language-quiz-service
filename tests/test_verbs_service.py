"""Unit tests for the verb service."""

import json
from unittest.mock import MagicMock

import pytest

from src.services.verb_service import VerbService
from src.schemas.verbs import VerbCreate, VerbUpdate, Verb
from src.prompts.verb_prompts import VerbPromptGenerator


@pytest.mark.unit
@pytest.mark.asyncio
class TestVerbService:
    """Test cases for the VerbService."""

    @pytest.fixture
    def service(
        self,
        mock_openai_client: MagicMock,
        mock_verb_repository: MagicMock,
    ) -> VerbService:
        """Fixture to create a VerbService with mock dependencies."""
        return VerbService(
            openai_client=mock_openai_client,
            verb_repository=mock_verb_repository,
            prompt_generator=VerbPromptGenerator(),
        )

    async def test_create_verb_valid_data(
        self,
        service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests creating a verb with valid data."""
        mock_verb_repository.create_verb.return_value = sample_db_verb
        verb_create = VerbCreate(**sample_db_verb.model_dump())

        created_verb = await service.create_verb(verb_create)

        assert created_verb is not None
        assert created_verb.infinitive == sample_db_verb.infinitive
        mock_verb_repository.create_verb.assert_called_once_with(verb_create)

    async def test_get_verb_by_id(
        self,
        service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests retrieving a verb by its ID."""
        mock_verb_repository.get_verb.return_value = sample_db_verb

        verb = await service.get_verb(sample_db_verb.id)

        assert verb is not None
        assert verb.id == sample_db_verb.id
        mock_verb_repository.get_verb.assert_called_once_with(sample_db_verb.id)

    async def test_update_verb(
        self,
        service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests updating a verb."""
        update_data = VerbUpdate(translation="new translation")
        sample_db_verb.translation = "new translation"
        mock_verb_repository.update_verb.return_value = sample_db_verb

        updated_verb = await service.update_verb(sample_db_verb.id, update_data)

        assert updated_verb is not None
        assert updated_verb.translation == "new translation"
        mock_verb_repository.update_verb.assert_called_once_with(
            sample_db_verb.id, update_data
        )

    async def test_delete_verb(
        self,
        service: VerbService,
        mock_verb_repository: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests deleting a verb."""
        mock_verb_repository.get_verb.return_value = sample_db_verb
        mock_verb_repository.delete_verb.return_value = True

        result = await service.delete_verb(sample_db_verb.id)

        assert result is True
        mock_verb_repository.delete_conjugations_by_verb.assert_called_once()
        mock_verb_repository.delete_verb.assert_called_once_with(sample_db_verb.id)

    async def test_download_verb_ai_integration(
        self,
        service: VerbService,
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
        mock_verb_repository.create_verb.return_value = sample_db_verb

        verb = await service.download_verb(verb_infinitive)

        assert verb is not None
        assert verb.infinitive == verb_infinitive
        mock_openai_client.handle_request.assert_called_once()
        mock_verb_repository.create_verb.assert_called_once()

    async def test_download_verb_invalid_ai_response(
        self, service: VerbService, mock_openai_client: MagicMock
    ):
        """Tests handling of invalid JSON from the AI client."""
        mock_openai_client.handle_request.return_value = "invalid json"

        with pytest.raises(ValueError, match="Invalid AI response format"):
            await service.download_verb("parler")
