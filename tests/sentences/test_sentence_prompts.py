"""Tests for sentence prompt generation functionality."""

from uuid import UUID

import pytest

from src.prompts.sentence_prompts import SentencePromptGenerator
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    SentenceBase,
    Tense,
)
from src.schemas.verbs import AuxiliaryType, Verb, VerbClassification


@pytest.fixture
def prompt_generator():
    """Fixture for SentencePromptGenerator."""
    return SentencePromptGenerator()


@pytest.fixture
def sample_sentence_base():
    """Fixture for a sample SentenceBase."""
    return SentenceBase(
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
        source="test",
    )


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


@pytest.mark.unit
class TestSentencePromptGenerator:
    """Test class for SentencePromptGenerator."""

    def test_generate_sentence_prompt_includes_creativity_instructions(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test that the sentence prompt includes creativity instructions."""
        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        # Check for creativity instructions
        assert "CREATIVITY INSTRUCTIONS:" in prompt
        assert "Create diverse, interesting sentences" in prompt
        assert "varied vocabulary" in prompt
        assert "contextually interesting and realistic" in prompt

    def test_generate_sentence_prompt_includes_enum_value_instructions(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test that the prompt includes clear instructions about enum values."""
        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        # Check for enum value instructions
        assert '"direct_object": "none, masculine, feminine, or plural"' in prompt
        assert '"indirect_object": "none, masculine, feminine, or plural"' in prompt
        assert (
            '"negation": "none, pas, jamais, rien, personne, plus, aucune, or encore"'
            in prompt
        )

        # Check for field instructions
        assert "Field Instructions:" in prompt
        assert "Do NOT put actual object words" in prompt
        assert "Do NOT use positive adverbs like" in prompt

    def test_generate_sentence_prompt_correct_sentence_instructions(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test that correct sentences get appropriate instructions."""
        sample_sentence_base.is_correct = True

        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        assert "grammatically correct" in prompt
        assert "SUBTLE grammatical errors" not in prompt

    def test_generate_sentence_prompt_incorrect_sentence_instructions(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test that incorrect sentences get creativity-preserving instructions."""
        sample_sentence_base.is_correct = False

        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        assert "SUBTLE grammatical errors" in prompt
        assert "maintaining the same level of creativity" in prompt
        assert "just as elaborate, descriptive, and creative" in prompt
        assert "Do not make the sentence shorter or simpler" in prompt

    def test_generate_sentence_prompt_includes_verb_complements(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test that the prompt includes instructions about verb complements."""
        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        assert (
            "If the verb requires additional objects or infinitives afterwards, add some"
            in prompt
        )

    def test_generate_sentence_prompt_with_direct_object(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test prompt generation when direct object is specified."""
        sample_sentence_base.direct_object = DirectObject.FEMININE

        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        assert "compliment direct object" in prompt
        assert "feminine" in prompt

    def test_generate_sentence_prompt_with_indirect_object(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test prompt generation when indirect object is specified."""
        sample_sentence_base.indirect_object = IndirectObject.PLURAL

        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        assert "compliment indirect object" in prompt
        assert "plural" in prompt

    def test_generate_sentence_prompt_with_negation(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test prompt generation when negation is specified."""
        sample_sentence_base.negation = Negation.PAS

        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        assert "The sentence must contain the negation pas" in prompt

    def test_generate_correctness_prompt_structure(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
    ):
        """Test that the correctness prompt has proper structure."""
        prompt = prompt_generator.generate_correctness_prompt(
            sample_sentence_base, sample_verb
        )

        # Check for key elements
        assert "French grammar expert" in prompt
        assert "Review the following sentence" in prompt
        assert "Return JSON with these fields:" in prompt
        assert "is_valid" in prompt
        assert "actual_direct_object" in prompt
        assert "actual_indirect_object" in prompt
        assert "actual_negation" in prompt

    @pytest.mark.parametrize(
        "direct_object, indirect_object, negation, is_correct",
        [
            (DirectObject.NONE, IndirectObject.NONE, Negation.NONE, True),
            (DirectObject.MASCULINE, IndirectObject.NONE, Negation.NONE, True),
            (DirectObject.NONE, IndirectObject.FEMININE, Negation.NONE, True),
            (DirectObject.NONE, IndirectObject.NONE, Negation.PAS, True),
            (DirectObject.PLURAL, IndirectObject.MASCULINE, Negation.JAMAIS, False),
        ],
    )
    def test_generate_sentence_prompt_parameterized(
        self,
        prompt_generator: SentencePromptGenerator,
        sample_sentence_base: SentenceBase,
        sample_verb: Verb,
        direct_object: DirectObject,
        indirect_object: IndirectObject,
        negation: Negation,
        is_correct: bool,
    ):
        """Test prompt generation with various parameter combinations."""
        sample_sentence_base.direct_object = direct_object
        sample_sentence_base.indirect_object = indirect_object
        sample_sentence_base.negation = negation
        sample_sentence_base.is_correct = is_correct

        prompt = prompt_generator.generate_sentence_prompt(
            sample_sentence_base, sample_verb
        )

        # Basic structure checks
        assert "French grammar expert" in prompt
        assert "CREATIVITY INSTRUCTIONS:" in prompt
        assert "Field Instructions:" in prompt

        # Correctness-specific checks
        if is_correct:
            assert "grammatically correct" in prompt
        else:
            assert "SUBTLE grammatical errors" in prompt
            assert "maintaining the same level of creativity" in prompt
