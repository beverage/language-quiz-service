"""Tests for CLI sentence functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.cli.sentences.create import create_sentence
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    Sentence,
    Tense,
)
from src.schemas.verbs import Verb, AuxiliaryType, VerbClassification
from uuid import UUID


@pytest.fixture
def sample_verb():
    """Fixture for a sample Verb."""
    return Verb(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        infinitive="avoir",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        target_language_code="eng",
        translation="to have",
        past_participle="eu",
        present_participle="ayant",
        classification=VerbClassification.THIRD_GROUP,
        is_irregular=True,
        can_have_cod=True,
        can_have_coi=False,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
        last_used_at="2023-01-01T00:00:00Z",
    )


@pytest.fixture
def sample_sentence():
    """Fixture for a sample Sentence."""
    return Sentence(
        id=UUID("87654321-4321-8765-4321-876543218765"),
        target_language_code="eng",
        content="J'ai un livre.",
        translation="I have a book.",
        verb_id=UUID("12345678-1234-5678-1234-567812345678"),
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.MASCULINE,
        indirect_object=IndirectObject.NONE,
        negation=Negation.NONE,
        is_correct=True,
        source="ai_generated",
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
    )


@pytest.mark.unit
class TestCLISentences:
    """Test class for CLI sentence functionality."""

    @patch("src.cli.sentences.create.SentenceService")
    @patch("src.cli.sentences.create.VerbService")
    async def test_create_sentence_validate_false_by_default(
        self,
        mock_verb_service_class: MagicMock,
        mock_sentence_service_class: MagicMock,
        sample_verb: Verb,
        sample_sentence: Sentence,
    ):
        """Test that create_sentence calls generate_sentence with validate=False by default."""
        # Setup mocks
        mock_verb_service = AsyncMock()
        mock_sentence_service = AsyncMock()
        mock_verb_service_class.return_value = mock_verb_service
        mock_sentence_service_class.return_value = mock_sentence_service

        mock_verb_service.get_verb_by_infinitive.return_value = sample_verb
        mock_sentence_service.generate_sentence.return_value = sample_sentence

        # Call create_sentence without validate parameter
        result = await create_sentence(
            verb_infinitive="avoir",
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=True,
        )

        # Verify validate=False was passed (default)
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert call_args.kwargs["validate"] is False
        assert result == sample_sentence

    @patch("src.cli.sentences.create.SentenceService")
    @patch("src.cli.sentences.create.VerbService")
    async def test_create_sentence_validate_true_passed_through(
        self,
        mock_verb_service_class: MagicMock,
        mock_sentence_service_class: MagicMock,
        sample_verb: Verb,
        sample_sentence: Sentence,
    ):
        """Test that create_sentence passes validate=True parameter through."""
        # Setup mocks
        mock_verb_service = AsyncMock()
        mock_sentence_service = AsyncMock()
        mock_verb_service_class.return_value = mock_verb_service
        mock_sentence_service_class.return_value = mock_sentence_service

        mock_verb_service.get_verb_by_infinitive.return_value = sample_verb
        mock_sentence_service.generate_sentence.return_value = sample_sentence

        # Call create_sentence with validate=True
        result = await create_sentence(
            verb_infinitive="avoir",
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=True,
            validate=True,
        )

        # Verify validate=True was passed through
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert call_args.kwargs["validate"] is True
        assert result == sample_sentence

    @patch("src.cli.sentences.create.SentenceService")
    @patch("src.cli.sentences.create.VerbService")
    async def test_create_sentence_validation_failure_propagated(
        self,
        mock_verb_service_class: MagicMock,
        mock_sentence_service_class: MagicMock,
        sample_verb: Verb,
    ):
        """Test that validation failures are properly propagated from service to CLI."""
        # Setup mocks
        mock_verb_service = AsyncMock()
        mock_sentence_service = AsyncMock()
        mock_verb_service_class.return_value = mock_verb_service
        mock_sentence_service_class.return_value = mock_sentence_service

        mock_verb_service.get_verb_by_infinitive.return_value = sample_verb
        mock_sentence_service.generate_sentence.side_effect = ValueError(
            "Sentence validation failed: Test error"
        )

        # Call create_sentence with validate=True - should raise ValueError
        with pytest.raises(ValueError, match="Sentence validation failed: Test error"):
            await create_sentence(
                verb_infinitive="avoir",
                validate=True,
            )

        # Verify the service was called with validation enabled
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert call_args.kwargs["validate"] is True

    @patch("src.cli.sentences.create.SentenceService")
    @patch("src.cli.sentences.create.VerbService")
    async def test_create_sentence_cod_coi_parameter_adjustment_with_validation(
        self,
        mock_verb_service_class: MagicMock,
        mock_sentence_service_class: MagicMock,
        sample_verb: Verb,
        sample_sentence: Sentence,
    ):
        """Test that COD/COI parameter adjustment works with validation enabled."""
        # Setup mocks - verb that can't have COD
        verb_no_cod = Verb(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            infinitive="dormir",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            target_language_code="eng",
            translation="to sleep",
            past_participle="dormi",
            present_participle="dormant",
            classification=VerbClassification.THIRD_GROUP,
            is_irregular=True,
            can_have_cod=False,
            can_have_coi=False,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            last_used_at="2023-01-01T00:00:00Z",
        )

        mock_verb_service = AsyncMock()
        mock_sentence_service = AsyncMock()
        mock_verb_service_class.return_value = mock_verb_service
        mock_sentence_service_class.return_value = mock_sentence_service

        mock_verb_service.get_verb_by_infinitive.return_value = verb_no_cod
        mock_sentence_service.generate_sentence.return_value = sample_sentence

        # Call create_sentence with COD but verb can't have COD
        result = await create_sentence(
            verb_infinitive="dormir",
            direct_object=DirectObject.MASCULINE,  # This should be adjusted to NONE
            validate=True,
        )

        # Verify COD was adjusted to NONE and validation was enabled
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert call_args.kwargs["direct_object"] == DirectObject.NONE
        assert call_args.kwargs["validate"] is True
        assert result == sample_sentence
