"""Unit tests for the Sentence Service."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from src.repositories.sentence_repository import SentenceRepository
from src.services.sentence_service import SentenceService
from src.schemas.sentences import (
    DirectObject,
    IndirectPronoun,
    Negation,
    Pronoun,
    Sentence,
    SentenceCreate,
    SentenceUpdate,
    Tense,
)
from src.schemas.verbs import Verb
from src.services.verb_service import VerbService
from src.clients.openai_client import OpenAIClient
import json


@pytest.fixture
def mock_sentence_repository():
    """Fixture for a mocked SentenceRepository."""
    return MagicMock(spec=SentenceRepository)


@pytest.fixture
def mock_openai_client():
    """Fixture for a mocked OpenAIClient."""
    return MagicMock(spec=OpenAIClient)


@pytest.fixture
def sentence_service(
    mock_sentence_repository: MagicMock,
    mock_verb_service: MagicMock,
    mock_openai_client: MagicMock,
) -> SentenceService:
    """Fixture for a SentenceService with a mocked repository."""
    return SentenceService(
        sentence_repository=mock_sentence_repository,
        verb_service=mock_verb_service,
        openai_client=mock_openai_client,
    )


@pytest.fixture
def mock_verb_service():
    """Fixture for a mocked VerbService."""
    return MagicMock(spec=VerbService)


@pytest.mark.unit
class TestSentenceService:
    """Test suite for the SentenceService."""

    async def test_create_sentence(
        self,
        sentence_service: SentenceService,
        mock_sentence_repository: MagicMock,
        sample_db_sentence: Sentence,
    ):
        """Test creating a sentence."""
        mock_sentence_repository.create_sentence.return_value = sample_db_sentence
        sentence_create = SentenceCreate(**sample_db_sentence.model_dump())

        created_sentence = await sentence_service.create_sentence(sentence_create)

        assert created_sentence == sample_db_sentence
        mock_sentence_repository.create_sentence.assert_awaited_once_with(
            sentence_create
        )

    async def test_get_sentence(
        self,
        sentence_service: SentenceService,
        mock_sentence_repository: MagicMock,
        sample_db_sentence: Sentence,
    ):
        """Test getting a sentence by ID."""
        mock_sentence_repository.get_sentence.return_value = sample_db_sentence
        sentence_id = sample_db_sentence.id

        sentence = await sentence_service.get_sentence(sentence_id)

        assert sentence == sample_db_sentence
        mock_sentence_repository.get_sentence.assert_awaited_once_with(sentence_id)

    async def test_get_all_sentences(
        self,
        sentence_service: SentenceService,
        mock_sentence_repository: MagicMock,
        sample_db_sentence: Sentence,
    ):
        """Test getting all sentences."""
        mock_sentence_repository.get_all_sentences.return_value = [sample_db_sentence]

        sentences = await sentence_service.get_all_sentences()

        assert sentences == [sample_db_sentence]
        mock_sentence_repository.get_all_sentences.assert_awaited_once()

    async def test_update_sentence(
        self,
        sentence_service: SentenceService,
        mock_sentence_repository: MagicMock,
        sample_db_sentence: Sentence,
    ):
        """Test updating a sentence."""
        updated_sentence = sample_db_sentence.model_copy(
            update={"content": "new content"}
        )
        mock_sentence_repository.update_sentence.return_value = updated_sentence
        sentence_id = sample_db_sentence.id
        update_data = SentenceUpdate(content="new content")

        sentence = await sentence_service.update_sentence(sentence_id, update_data)

        assert sentence == updated_sentence
        mock_sentence_repository.update_sentence.assert_awaited_once_with(
            sentence_id, update_data
        )

    async def test_delete_sentence(
        self, sentence_service: SentenceService, mock_sentence_repository: MagicMock
    ):
        """Test deleting a sentence."""
        mock_sentence_repository.delete_sentence.return_value = True
        sentence_id = uuid.uuid4()

        result = await sentence_service.delete_sentence(sentence_id)

        assert result is True
        mock_sentence_repository.delete_sentence.assert_awaited_once_with(sentence_id)

    async def test_generate_sentence_incorrect_from_ai(
        self,
        sentence_service: SentenceService,
        mock_verb_service: MagicMock,
        mock_openai_client: MagicMock,
        mock_sentence_repository: MagicMock,
        sample_db_verb: Verb,
        sample_db_sentence: Sentence,
    ):
        """Test generating a sentence that the AI marks as incorrect."""
        verb_id = sample_db_verb.id
        mock_verb_service.get_verb.return_value = sample_db_verb

        ai_response = {
            "sentence": "This is a wrong sentence.",
            "translation": "Ceci est une phrase incorrecte.",
            "is_correct": False,
            "explanation": "The verb conjugation is wrong.",
            "negation": "none",
        }
        mock_openai_client.handle_request.return_value = json.dumps(ai_response)

        # We need to create a sentence object that reflects the AI response for assertion
        expected_created_sentence = sample_db_sentence.model_copy(
            update={
                "content": ai_response["sentence"],
                "translation": ai_response["translation"],
                "is_correct": False,
                "explanation": ai_response["explanation"],
            }
        )
        mock_sentence_repository.create_sentence.return_value = (
            expected_created_sentence
        )

        generated_sentence = await sentence_service.generate_sentence(verb_id=verb_id)

        assert not generated_sentence.is_correct
        assert generated_sentence.explanation == "The verb conjugation is wrong."

        # Verify that the data passed to create_sentence is correct
        call_args = mock_sentence_repository.create_sentence.call_args[0][0]
        assert isinstance(call_args, SentenceCreate)
        assert call_args.is_correct is False
        assert call_args.explanation == "The verb conjugation is wrong."

    async def test_generate_sentence_with_ai_modifications(
        self,
        sentence_service: SentenceService,
        mock_verb_service: MagicMock,
        mock_openai_client: MagicMock,
        mock_sentence_repository: MagicMock,
        sample_db_verb: Verb,
        sample_db_sentence: Sentence,
    ):
        """Test generating a sentence where the AI modifies grammatical elements."""
        verb_id = sample_db_verb.id
        mock_verb_service.get_verb.return_value = sample_db_verb

        ai_response = {
            "sentence": "Il ne le leur a jamais dit.",
            "translation": "He never told it to them.",
            "is_correct": "true",  # Test string boolean
            "direct_object": "masculine",
            "indirect_pronoun": "plural",
            "negation": "jamais",
            "has_compliment_object_direct": True,
            "has_compliment_object_indirect": True,
        }
        mock_openai_client.handle_request.return_value = json.dumps(ai_response)

        expected_sentence = sample_db_sentence.model_copy(update=ai_response)
        mock_sentence_repository.create_sentence.return_value = expected_sentence

        await sentence_service.generate_sentence(verb_id=verb_id)

        # Verify that create_sentence was called with the modified values
        call_args = mock_sentence_repository.create_sentence.call_args[0][0]
        assert isinstance(call_args, SentenceCreate)
        assert call_args.is_correct is True
        assert call_args.direct_object == DirectObject.MASCULINE
        assert call_args.indirect_pronoun == IndirectPronoun.PLURAL
        assert call_args.negation == Negation.JAMAIS

    @pytest.mark.parametrize(
        "pronoun, tense, direct_object, indirect_pronoun, negation",
        [
            (
                Pronoun.FIRST_PERSON,
                Tense.PRESENT,
                DirectObject.NONE,
                IndirectPronoun.NONE,
                Negation.NONE,
            ),
            (
                Pronoun.SECOND_PERSON_PLURAL,
                Tense.FUTURE_SIMPLE,
                DirectObject.MASCULINE,
                IndirectPronoun.NONE,
                Negation.PAS,
            ),
            (
                Pronoun.THIRD_PERSON,
                Tense.PASSE_COMPOSE,
                DirectObject.FEMININE,
                IndirectPronoun.PLURAL,
                Negation.JAMAIS,
            ),
        ],
    )
    async def test_generate_sentence_parameterized(
        self,
        sentence_service: SentenceService,
        mock_verb_service: MagicMock,
        mock_openai_client: MagicMock,
        mock_sentence_repository: MagicMock,
        sample_db_verb: Verb,
        sample_db_sentence: Sentence,
        pronoun: Pronoun,
        tense: Tense,
        direct_object: DirectObject,
        indirect_pronoun: IndirectPronoun,
        negation: Negation,
    ):
        """Test generating a sentence with different parameters."""
        verb_id = sample_db_verb.id
        mock_verb_service.get_verb.return_value = sample_db_verb

        ai_response = {
            "sentence": sample_db_sentence.content,
            "translation": sample_db_sentence.translation,
            "is_correct": True,
            "negation": "none",
        }
        mock_openai_client.handle_request.return_value = json.dumps(ai_response)
        mock_sentence_repository.create_sentence.return_value = sample_db_sentence

        generated_sentence = await sentence_service.generate_sentence(
            verb_id=verb_id,
            pronoun=pronoun,
            tense=tense,
            direct_object=direct_object,
            indirect_pronoun=indirect_pronoun,
            negation=negation,
        )

        assert generated_sentence == sample_db_sentence
        mock_verb_service.get_verb.assert_awaited_with(verb_id)
        mock_openai_client.handle_request.assert_awaited_once()
        mock_sentence_repository.create_sentence.assert_awaited_once()

    async def test_generate_sentence_verb_not_found(
        self, sentence_service: SentenceService, mock_verb_service: MagicMock
    ):
        """Test generate_sentence when the verb is not found."""
        verb_id = uuid.uuid4()
        mock_verb_service.get_verb.return_value = None

        with pytest.raises(ValueError, match=f"Verb with ID {verb_id} not found"):
            await sentence_service.generate_sentence(verb_id=verb_id)

    async def test_generate_random_sentence_success(
        self,
        sentence_service: SentenceService,
        mock_verb_service: MagicMock,
        mock_openai_client: MagicMock,
        mock_sentence_repository: MagicMock,
        sample_db_verb: Verb,
        sample_db_sentence: Sentence,
    ):
        """Test generating a random sentence successfully."""
        mock_verb_service.get_random_verb.return_value = sample_db_verb

        ai_response = {
            "sentence": sample_db_sentence.content,
            "translation": sample_db_sentence.translation,
            "is_correct": True,
            "negation": "none",
        }
        mock_openai_client.handle_request.return_value = json.dumps(ai_response)
        mock_sentence_repository.create_sentence.return_value = sample_db_sentence

        generated_sentence = await sentence_service.generate_random_sentence()

        assert generated_sentence == sample_db_sentence
        mock_verb_service.get_random_verb.assert_awaited_once()
        mock_openai_client.handle_request.assert_awaited_once()
        mock_sentence_repository.create_sentence.assert_awaited_once()

    async def test_generate_random_sentence_no_verbs(
        self, sentence_service: SentenceService, mock_verb_service: MagicMock
    ):
        """Test generate_random_sentence when no verbs are available."""
        mock_verb_service.get_random_verb.return_value = None

        with pytest.raises(
            ValueError, match="No verbs available for sentence generation"
        ):
            await sentence_service.generate_random_sentence()

    async def test_generate_random_sentence_with_negation(
        self,
        sentence_service: SentenceService,
        mock_verb_service: MagicMock,
        mock_openai_client: MagicMock,
        mock_sentence_repository: MagicMock,
        sample_db_verb: Verb,
        sample_db_sentence: Sentence,
    ):
        """Test that generate_random_sentence can produce a negated sentence."""
        mock_verb_service.get_random_verb.return_value = sample_db_verb
        ai_response = {
            "sentence": "test",
            "translation": "test",
            "is_correct": True,
            "negation": "pas",
        }
        mock_openai_client.handle_request.return_value = json.dumps(ai_response)
        mock_sentence_repository.create_sentence.return_value = sample_db_sentence

        with patch("src.services.sentence_service.random") as mock_random:
            mock_random.randint.return_value = 8  # Force negation path
            mock_random.choice.side_effect = [
                Pronoun.FIRST_PERSON,
                Tense.PRESENT,
                DirectObject.NONE,
                IndirectPronoun.NONE,
                Negation.PAS,  # The chosen negation
            ]

            await sentence_service.generate_random_sentence()

        call_args = mock_sentence_repository.create_sentence.call_args[0][0]
        assert isinstance(call_args, SentenceCreate)
        assert call_args.negation == Negation.PAS

    async def test_generate_random_sentence_without_negation(
        self,
        sentence_service: SentenceService,
        mock_verb_service: MagicMock,
        mock_openai_client: MagicMock,
        mock_sentence_repository: MagicMock,
        sample_db_verb: Verb,
        sample_db_sentence: Sentence,
    ):
        """Test that generate_random_sentence can produce a non-negated sentence."""
        mock_verb_service.get_random_verb.return_value = sample_db_verb
        ai_response = {
            "sentence": "test",
            "translation": "test",
            "is_correct": True,
            "negation": "none",
        }
        mock_openai_client.handle_request.return_value = json.dumps(ai_response)
        mock_sentence_repository.create_sentence.return_value = sample_db_sentence

        with patch("src.services.sentence_service.random") as mock_random:
            mock_random.randint.return_value = 5  # Force non-negation path
            mock_random.choice.side_effect = [
                Pronoun.FIRST_PERSON,
                Tense.PRESENT,
                DirectObject.NONE,
                IndirectPronoun.NONE,
            ]

            await sentence_service.generate_random_sentence()

        call_args = mock_sentence_repository.create_sentence.call_args[0][0]
        assert isinstance(call_args, SentenceCreate)
        assert call_args.negation == Negation.NONE
        assert mock_random.choice.call_count == 4
