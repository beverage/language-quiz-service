"""Tests for compositional prompt builder."""

import uuid
from datetime import datetime

import pytest

from src.prompts.compositional_prompts import (
    CompositionalPromptBuilder,
    ErrorType,
)
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    SentenceBase,
)
from src.schemas.verbs import AuxiliaryType, Tense, Verb


@pytest.fixture
def builder():
    """Create a prompt builder instance."""
    return CompositionalPromptBuilder()


@pytest.fixture
def avoir_verb():
    """Create a test verb with avoir auxiliary."""
    return Verb(
        id=uuid.uuid4(),
        infinitive="parler",
        translation="to speak",
        past_participle="parlé",
        present_participle="parlant",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        target_language_code="eng",
        can_have_cod=True,
        can_have_coi=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def etre_verb():
    """Create a test verb with être auxiliary."""
    return Verb(
        id=uuid.uuid4(),
        infinitive="aller",
        translation="to go",
        past_participle="allé",
        present_participle="allant",
        auxiliary=AuxiliaryType.ETRE,
        reflexive=False,
        target_language_code="eng",
        can_have_cod=False,
        can_have_coi=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def base_sentence():
    """Create a base sentence configuration."""
    return SentenceBase(
        content="",
        translation="",
        verb_id=uuid.uuid4(),
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.NONE,
        indirect_object=IndirectObject.NONE,
        negation=Negation.NONE,
        is_correct=True,
    )


class TestCorrectSentencePrompt:
    """Tests for correct sentence prompt generation."""

    def test_generates_correct_prompt(self, builder, avoir_verb, base_sentence):
        """Test that correct sentence prompt is generated."""
        prompt = builder.build_correct_sentence_prompt(base_sentence, avoir_verb)

        assert "grammatically CORRECT sentence" in prompt
        assert "parler" in prompt
        assert "je" in prompt
        assert "present" in prompt
        assert "explanation as an empty string" in prompt

    def test_includes_verb_details(self, builder, avoir_verb, base_sentence):
        """Test that verb details are included."""
        prompt = builder.build_correct_sentence_prompt(base_sentence, avoir_verb)

        assert avoir_verb.infinitive in prompt
        assert avoir_verb.translation in prompt
        assert avoir_verb.past_participle in prompt
        assert "avoir" in prompt

    def test_includes_negation_when_present(self, builder, avoir_verb, base_sentence):
        """Test that negation is included when specified."""
        base_sentence.negation = Negation.PAS
        prompt = builder.build_correct_sentence_prompt(base_sentence, avoir_verb)

        assert "pas" in prompt


class TestWrongConjugationPrompt:
    """Tests for wrong conjugation error prompt generation."""

    def test_generates_wrong_conjugation_prompt(
        self, builder, avoir_verb, base_sentence
    ):
        """Test that wrong conjugation prompt is generated."""
        base_sentence.is_correct = False
        prompt = builder.build_wrong_conjugation_prompt(base_sentence, avoir_verb)

        assert "INCORRECT verb conjugation" in prompt
        assert "parler" in prompt
        assert "je" in prompt
        assert "WRONG" in prompt.upper()

    def test_includes_forbidden_form_when_provided(
        self, builder, avoir_verb, base_sentence
    ):
        """Test that correct conjugation is marked as forbidden."""
        base_sentence.is_correct = False
        correct_conjugation = "parles"

        prompt = builder.build_wrong_conjugation_prompt(
            base_sentence, avoir_verb, correct_conjugation=correct_conjugation
        )

        assert "FORBIDDEN" in prompt
        assert correct_conjugation in prompt
        assert "spelled DIFFERENTLY" in prompt

    def test_no_forbidden_section_without_conjugation(
        self, builder, avoir_verb, base_sentence
    ):
        """Test that forbidden section is omitted when conjugation not provided."""
        base_sentence.is_correct = False

        prompt = builder.build_wrong_conjugation_prompt(
            base_sentence, avoir_verb, correct_conjugation=None
        )

        assert "FORBIDDEN" not in prompt


class TestErrorTypeSelection:
    """Tests for error type selection logic."""

    def test_only_conjugation_for_simple_present(
        self, builder, avoir_verb, base_sentence
    ):
        """Test that only conjugation error is available for simple present."""
        base_sentence.is_correct = False

        errors = builder.select_error_types(base_sentence, avoir_verb, count=3)

        # Only conjugation available for present tense with no COD/COI
        assert len(errors) == 1
        assert ErrorType.WRONG_CONJUGATION in errors

    def test_cod_error_not_selected_when_disabled(
        self, builder, avoir_verb, base_sentence
    ):
        """Test that COD errors are not selected (currently disabled)."""
        base_sentence.is_correct = False
        base_sentence.direct_object = DirectObject.MASCULINE

        errors = builder.select_error_types(base_sentence, avoir_verb, count=3)

        # COD errors currently disabled
        assert ErrorType.COD_PRONOUN_ERROR not in errors

    def test_auxiliary_error_for_passe_compose(
        self, builder, avoir_verb, base_sentence
    ):
        """Test that auxiliary error is available for passé composé."""
        base_sentence.is_correct = False
        base_sentence.tense = Tense.PASSE_COMPOSE

        errors = builder.select_error_types(base_sentence, avoir_verb, count=3)

        assert ErrorType.WRONG_AUXILIARY in errors
        assert ErrorType.WRONG_CONJUGATION in errors

    def test_past_participle_for_etre_verbs(self, builder, etre_verb, base_sentence):
        """Test that past participle agreement error is available for être verbs."""
        base_sentence.is_correct = False
        base_sentence.tense = Tense.PASSE_COMPOSE
        base_sentence.pronoun = Pronoun.THIRD_PERSON  # Unambiguous gender

        errors = builder.select_error_types(base_sentence, etre_verb, count=3)

        assert ErrorType.PAST_PARTICIPLE_AGREEMENT in errors

    def test_past_participle_excluded_for_ambiguous_pronouns(
        self, builder, etre_verb, base_sentence
    ):
        """Test that past participle error excluded for je/tu/nous/vous."""
        base_sentence.is_correct = False
        base_sentence.tense = Tense.PASSE_COMPOSE

        # Test all ambiguous pronouns
        ambiguous = [
            Pronoun.FIRST_PERSON,
            Pronoun.SECOND_PERSON,
            Pronoun.FIRST_PERSON_PLURAL,
            Pronoun.SECOND_PERSON_PLURAL,
        ]

        for pronoun in ambiguous:
            base_sentence.pronoun = pronoun
            errors = builder.select_error_types(base_sentence, etre_verb, count=3)

            # Past participle agreement should not be available
            assert ErrorType.PAST_PARTICIPLE_AGREEMENT not in errors


class TestBuildPromptRouting:
    """Tests for build_prompt method routing."""

    def test_routes_to_correct_prompt(self, builder, avoir_verb, base_sentence):
        """Test that correct sentences route to correct prompt builder."""
        base_sentence.is_correct = True

        prompt = builder.build_prompt(base_sentence, avoir_verb)

        assert "grammatically CORRECT" in prompt

    def test_routes_to_conjugation_error(self, builder, avoir_verb, base_sentence):
        """Test routing to conjugation error prompt."""
        base_sentence.is_correct = False

        prompt = builder.build_prompt(
            base_sentence, avoir_verb, error_type=ErrorType.WRONG_CONJUGATION
        )

        assert "INCORRECT verb conjugation" in prompt

    def test_routes_to_auxiliary_error(self, builder, avoir_verb, base_sentence):
        """Test routing to auxiliary error prompt."""
        base_sentence.is_correct = False
        base_sentence.tense = Tense.PASSE_COMPOSE

        prompt = builder.build_prompt(
            base_sentence, avoir_verb, error_type=ErrorType.WRONG_AUXILIARY
        )

        assert "WRONG auxiliary verb" in prompt

    def test_requires_error_type_for_incorrect(
        self, builder, avoir_verb, base_sentence
    ):
        """Test that error_type is required for incorrect sentences."""
        base_sentence.is_correct = False

        with pytest.raises(ValueError, match="error_type must be provided"):
            builder.build_prompt(base_sentence, avoir_verb, error_type=None)


class TestPronounDisplay:
    """Tests for pronoun display conversion."""

    def test_converts_all_pronouns(self, builder):
        """Test that all pronouns convert correctly."""
        conversions = {
            Pronoun.FIRST_PERSON: "je",
            Pronoun.SECOND_PERSON: "tu",
            Pronoun.THIRD_PERSON: "il/elle",
            Pronoun.FIRST_PERSON_PLURAL: "nous",
            Pronoun.SECOND_PERSON_PLURAL: "vous",
            Pronoun.THIRD_PERSON_PLURAL: "ils/elles",
        }

        for pronoun, expected in conversions.items():
            result = builder._get_pronoun_display(pronoun.value)
            assert result == expected


class TestResponseFormat:
    """Tests for JSON response format section."""

    def test_includes_response_format(self, builder, avoir_verb, base_sentence):
        """Test that response format is included in all prompts."""
        prompt = builder.build_correct_sentence_prompt(base_sentence, avoir_verb)

        assert "RESPONSE FORMAT" in prompt
        assert "JSON" in prompt
        assert '"sentence"' in prompt
        assert '"translation"' in prompt
        assert '"explanation"' in prompt


class TestCreativitySection:
    """Tests for creativity requirements."""

    def test_includes_creativity_requirements(self, builder, avoir_verb, base_sentence):
        """Test that creativity section is included."""
        prompt = builder.build_correct_sentence_prompt(base_sentence, avoir_verb)

        assert "CREATIVITY" in prompt
        assert "varied vocabulary" in prompt
        assert "realistic" in prompt
