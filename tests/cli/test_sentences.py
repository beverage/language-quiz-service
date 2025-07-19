"""Tests for CLI sentence functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from asyncclick.testing import CliRunner

from src.cli.sentences.create import create_sentence
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    Sentence,
    Tense,
)
from src.schemas.verbs import AuxiliaryType, Verb, VerbClassification


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

        # Use CliRunner to invoke the command
        runner = CliRunner()
        result = await runner.invoke(
            create_sentence,
            [
                "avoir",  # verb_infinitive is a positional argument
                "--pronoun",
                "first_person",
                "--tense",
                "present",
                "--direct_object",
                "none",
                "--indirect_object",
                "none",
                "--negation",
                "none",
                "--is_correct",
                "true",
            ],
        )

        # Verify command executed successfully
        assert result.exit_code == 0

        # Verify validate=False was passed (default)
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert call_args.kwargs["validate"] is False

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

        # Use CliRunner to invoke the command with validate=True
        runner = CliRunner()
        result = await runner.invoke(
            create_sentence,
            [
                "avoir",  # verb_infinitive is a positional argument
                "--pronoun",
                "first_person",
                "--tense",
                "present",
                "--direct_object",
                "none",
                "--indirect_object",
                "none",
                "--negation",
                "none",
                "--is_correct",
                "true",
                "--validate",
                "true",
            ],
        )

        # Verify command executed successfully
        assert result.exit_code == 0

        # Verify validate=True was passed through
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert call_args.kwargs["validate"] is True

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

        # Use CliRunner to invoke the command with validation enabled
        runner = CliRunner()
        result = await runner.invoke(
            create_sentence,
            [
                "avoir",  # verb_infinitive is a positional argument
                "--validate",
                "true",
            ],
        )

        # Verify command failed with non-zero exit code
        assert result.exit_code != 0

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

        # Use CliRunner to invoke the command with COD but verb can't have COD
        runner = CliRunner()
        result = await runner.invoke(
            create_sentence,
            [
                "dormir",  # verb_infinitive is a positional argument
                "--direct_object",
                "masculine",  # This should be adjusted to NONE
                "--validate",
                "true",
            ],
        )

        # Verify command executed successfully
        assert result.exit_code == 0

        # Verify COD was adjusted to NONE and validation was enabled
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert call_args.kwargs["direct_object"] == DirectObject.NONE
        assert call_args.kwargs["validate"] is True
