"""Unit tests for the SentencePromptGenerator."""

import pytest
from src.prompts.sentence_prompts import SentencePromptGenerator
from src.schemas.sentences import Sentence, DirectObject, IndirectPronoun, Negation
from unittest.mock import MagicMock
from unittest.mock import patch


@pytest.fixture
def prompt_generator():
    """Fixture for the SentencePromptGenerator."""
    return SentencePromptGenerator()


@pytest.fixture
def mock_sentence():
    """Fixture for a mock Sentence object."""
    sentence = MagicMock(spec=Sentence)
    sentence.is_correct = True
    sentence.direct_object = DirectObject.NONE
    sentence.indirect_pronoun = IndirectPronoun.NONE
    sentence.negation = Negation.NONE
    sentence.target_language_code = "eng"  # Add the missing attribute
    return sentence


@pytest.mark.asyncio
async def test_correctness_prompt(
    prompt_generator: SentencePromptGenerator, mock_sentence: MagicMock
):
    """Tests the __correctness private method."""
    # Test for correct sentence
    mock_sentence.is_correct = True
    result = prompt_generator._SentencePromptGenerator__correctness(mock_sentence)
    assert "grammatically correct" in result

    # Test for incorrect sentence
    mock_sentence.is_correct = False
    result = prompt_generator._SentencePromptGenerator__correctness(mock_sentence)
    assert "grammatical errors" in result

    # Test for incorrect sentence with direct object
    mock_sentence.direct_object = DirectObject.MASCULINE
    result = prompt_generator._SentencePromptGenerator__correctness(mock_sentence)
    assert "complement object should be incorrect" in result

    # Test for incorrect sentence with indirect pronoun
    mock_sentence.direct_object = DirectObject.NONE
    mock_sentence.indirect_pronoun = IndirectPronoun.PLURAL
    result = prompt_generator._SentencePromptGenerator__correctness(mock_sentence)
    assert "indirect pronoun should be incorrect" in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "has_cod, has_coi, has_negation, is_correct, expected_calls",
    [
        (False, False, False, True, ["__sentence_properties"]),
        (
            True,
            False,
            False,
            True,
            ["__sentence_properties", "__compliment_object_direct"],
        ),
        (
            False,
            True,
            False,
            True,
            ["__sentence_properties", "__compliment_object_indirect"],
        ),
        (False, False, True, True, ["__sentence_properties", "__negation"]),
        (False, False, False, False, ["__sentence_properties", "__correctness"]),
        (
            True,
            True,
            True,
            False,
            [
                "__sentence_properties",
                "__compliment_object_direct",
                "__compliment_object_indirect",
                "__negation",
                "__correctness",
            ],
        ),
    ],
)
async def test_generate_sentence_prompt_logic(
    prompt_generator: SentencePromptGenerator,
    mock_sentence: MagicMock,
    has_cod,
    has_coi,
    has_negation,
    is_correct,
    expected_calls,
):
    """Tests the conditional logic of generate_sentence_prompt."""
    mock_sentence.direct_object = (
        DirectObject.MASCULINE if has_cod else DirectObject.NONE
    )
    mock_sentence.indirect_pronoun = (
        IndirectPronoun.PLURAL if has_coi else IndirectPronoun.NONE
    )
    mock_sentence.negation = Negation.PAS if has_negation else Negation.NONE
    mock_sentence.is_correct = is_correct

    mock_verb = MagicMock()

    with patch.object(
        prompt_generator,
        "_SentencePromptGenerator__sentence_properties",
        return_value="",
    ) as mock_sp, patch.object(
        prompt_generator,
        "_SentencePromptGenerator__compliment_object_direct",
        return_value="",
    ) as mock_cod, patch.object(
        prompt_generator,
        "_SentencePromptGenerator__compliment_object_indirect",
        return_value="",
    ) as mock_coi, patch.object(
        prompt_generator, "_SentencePromptGenerator__negation", return_value=""
    ) as mock_neg, patch.object(
        prompt_generator, "_SentencePromptGenerator__correctness", return_value=""
    ) as mock_corr:
        prompt_generator.generate_sentence_prompt(mock_sentence, mock_verb)

        all_mocks = {
            "__sentence_properties": mock_sp,
            "__compliment_object_direct": mock_cod,
            "__compliment_object_indirect": mock_coi,
            "__negation": mock_neg,
            "__correctness": mock_corr,
        }

        for name, mock_func in all_mocks.items():
            if name in expected_calls:
                mock_func.assert_called_once()
            else:
                mock_func.assert_not_called()
