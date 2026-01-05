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

    @patch("src.cli.sentences.create.create_sentence_service")
    @patch("src.cli.sentences.create.create_verb_service")
    async def test_create_sentence_basic_flow(
        self,
        mock_create_verb_service: MagicMock,
        mock_create_sentence_service: MagicMock,
        sample_verb: Verb,
        sample_sentence: Sentence,
    ):
        """Test that create_sentence calls generate_sentence with the correct parameters."""
        # Setup mocks
        mock_verb_service = AsyncMock()
        mock_sentence_service = AsyncMock()
        mock_create_verb_service.return_value = mock_verb_service
        mock_create_sentence_service.return_value = mock_sentence_service

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

        # Verify sentence was created (validate param should not exist anymore)
        mock_sentence_service.generate_sentence.assert_called_once()
        call_args = mock_sentence_service.generate_sentence.call_args
        assert "validate" not in call_args.kwargs
