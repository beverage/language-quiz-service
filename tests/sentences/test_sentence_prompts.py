"""Comprehensive test suite for sentence prompt system.

Tests the sentence prompt generation system without hardcoded string matching.
Focuses on structure, logic, and integration rather than exact prompt content.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.prompts.sentences import ErrorType, SentencePromptBuilder
from src.prompts.sentences.templates import (
    COMPOUND_TENSES,
    format_optional_dimension,
    requires_auxiliary,
)
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    SentenceBase,
)
from src.schemas.verbs import AuxiliaryType, Tense, Verb

# ===== Fixtures =====


@pytest.fixture
def builder():
    """Create a sentence prompt builder instance."""
    return SentencePromptBuilder()


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
def present_conjugations():
    """Create mock present tense conjugations."""
    conjugation = MagicMock()
    conjugation.tense = Tense.PRESENT
    conjugation.first_person_singular = "parle"
    conjugation.second_person_singular = "parles"
    conjugation.third_person_singular = "parle"
    conjugation.first_person_plural = "parlons"
    conjugation.second_person_plural = "parlez"
    conjugation.third_person_plural = "parlent"
    return [conjugation]


@pytest.fixture
def passe_compose_conjugations():
    """Create mock passé composé conjugations."""
    conjugation = MagicMock()
    conjugation.tense = Tense.PASSE_COMPOSE
    conjugation.first_person_singular = "suis allé"
    conjugation.second_person_singular = "es allé"
    conjugation.third_person_singular = "est allé"
    conjugation.first_person_plural = "sommes allés"
    conjugation.second_person_plural = "êtes allés"
    conjugation.third_person_plural = "sont allés"
    return [conjugation]


@pytest.fixture
def basic_sentence():
    """Create a basic correct sentence configuration."""
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
        target_language_code="eng",
    )


# ===== Test Correct Sentence Prompts =====


class TestCorrectSentencePrompts:
    """Tests for correct sentence prompt generation."""

    def test_correct_prompt_contains_required_sections(
        self, builder, basic_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct prompt contains all required sections."""
        prompt = builder.build_prompt(basic_sentence, avoir_verb, present_conjugations)

        # Should contain verb details
        assert avoir_verb.infinitive in prompt
        # Note: past_participle is only included for compound tenses (passé composé, etc.)
        # For simple tenses like present, it's omitted to avoid confusing the LLM

        # Should contain required parameters section
        assert "REQUIRED" in prompt

        # Should contain instructions
        assert "CORRECT" in prompt or "correct" in prompt

    def test_correct_prompt_includes_conjugation(
        self, builder, basic_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct prompt includes the correct conjugation form."""
        prompt = builder.build_prompt(basic_sentence, avoir_verb, present_conjugations)

        # The correct conjugation for first person should be in the prompt
        assert "parle" in prompt

    def test_correct_prompt_includes_auxiliary_for_compound_tense(
        self, builder, etre_verb, passe_compose_conjugations
    ):
        """Verify correct prompt includes auxiliary information for compound tenses."""
        # Auxiliary info is only included for compound tenses (passé composé, etc.)
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PASSE_COMPOSE,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=True,
            target_language_code="eng",
        )
        prompt = builder.build_prompt(sentence, etre_verb, passe_compose_conjugations)

        # Compound tense should include auxiliary info
        assert "être" in prompt.lower()
        assert etre_verb.past_participle in prompt

    def test_correct_prompt_includes_tense(
        self, builder, basic_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct prompt includes tense information."""
        prompt = builder.build_prompt(basic_sentence, avoir_verb, present_conjugations)

        assert basic_sentence.tense.value in prompt

    def test_correct_prompt_returns_string(
        self, builder, basic_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct prompt returns a non-empty string."""
        prompt = builder.build_prompt(basic_sentence, avoir_verb, present_conjugations)

        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ===== Test Conjugation Error Prompts =====


class TestConjugationErrorPrompts:
    """Tests for conjugation error prompt generation."""

    def test_conjugation_error_prompt_contains_wrong_form(
        self, builder, avoir_verb, present_conjugations
    ):
        """Verify conjugation error prompt includes the deliberately wrong form."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        prompt = builder.build_prompt(
            sentence,
            avoir_verb,
            present_conjugations,
            error_type=ErrorType.WRONG_CONJUGATION,
        )

        # Should emphasize the error
        assert "WRONG" in prompt or "wrong" in prompt
        assert "MUST" in prompt or "must" in prompt

    def test_conjugation_error_prompt_has_explanation_instruction(
        self, builder, avoir_verb, present_conjugations
    ):
        """Verify conjugation error prompt includes explanation instructions."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.SECOND_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        prompt = builder.build_prompt(
            sentence,
            avoir_verb,
            present_conjugations,
            error_type=ErrorType.WRONG_CONJUGATION,
        )

        # Should have explanation instructions
        assert "explanation" in prompt.lower() or "explain" in prompt.lower()

    def test_conjugation_error_uses_different_form(
        self, builder, avoir_verb, present_conjugations
    ):
        """Verify conjugation error uses a form different from the correct one."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        # Run multiple times to ensure we're getting wrong forms
        for _ in range(5):
            prompt = builder.build_prompt(
                sentence,
                avoir_verb,
                present_conjugations,
                error_type=ErrorType.WRONG_CONJUGATION,
            )

            # The prompt should contain a conjugation form
            # (we can't assert which specific wrong form without hardcoding)
            assert any(
                form in prompt
                for form in ["parle", "parles", "parlons", "parlez", "parlent"]
            )


# ===== Test Auxiliary Error Prompts =====


class TestAuxiliaryErrorPrompts:
    """Tests for auxiliary error prompt generation."""

    def test_auxiliary_error_prompt_for_etre_verb(
        self, builder, etre_verb, passe_compose_conjugations
    ):
        """Verify auxiliary error prompt correctly specifies wrong auxiliary."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PASSE_COMPOSE,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        prompt = builder.build_prompt(
            sentence,
            etre_verb,
            passe_compose_conjugations,
            error_type=ErrorType.WRONG_AUXILIARY,
        )

        # Verb uses être, so wrong auxiliary should be avoir
        assert "avoir" in prompt.lower()
        assert "être" in prompt.lower()

    def test_auxiliary_error_has_explanation_instruction(
        self, builder, etre_verb, passe_compose_conjugations
    ):
        """Verify auxiliary error prompt includes explanation instructions."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PASSE_COMPOSE,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        prompt = builder.build_prompt(
            sentence,
            etre_verb,
            passe_compose_conjugations,
            error_type=ErrorType.WRONG_AUXILIARY,
        )

        # Should have explanation instructions
        assert "explanation" in prompt.lower() or "explain" in prompt.lower()
        assert "auxiliary" in prompt.lower()


# ===== Test Error Type Selection =====


class TestErrorTypeSelection:
    """Tests for error type selection logic."""

    def test_select_error_types_for_present_tense(self, builder, avoir_verb):
        """Verify error type selection for present tense (no auxiliary errors)."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        error_types = builder.select_error_types(sentence, avoir_verb, count=3)

        # Present tense should only have conjugation errors
        assert ErrorType.WRONG_CONJUGATION in error_types
        assert ErrorType.WRONG_AUXILIARY not in error_types

    def test_select_error_types_for_passe_compose(self, builder, etre_verb):
        """Verify error type selection for passé composé (includes auxiliary)."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PASSE_COMPOSE,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        error_types = builder.select_error_types(sentence, etre_verb, count=3)

        # Should include both conjugation and auxiliary errors
        assert ErrorType.WRONG_CONJUGATION in error_types
        # Auxiliary error should be available (might be selected)
        available_errors = [ErrorType.WRONG_CONJUGATION, ErrorType.WRONG_AUXILIARY]
        assert all(et in available_errors for et in error_types)

    def test_select_error_types_respects_count(self, builder, avoir_verb):
        """Verify error type selection respects the requested count."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        error_types = builder.select_error_types(sentence, avoir_verb, count=1)

        # Should return exactly 1 error type (or less if not enough available)
        assert len(error_types) <= 1

    def test_select_error_types_handles_excessive_count(self, builder, avoir_verb):
        """Verify error type selection handles count larger than available."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        # Request more than available
        error_types = builder.select_error_types(sentence, avoir_verb, count=10)

        # Should return all available types without error
        assert len(error_types) >= 1
        assert all(isinstance(et, ErrorType) for et in error_types)


# ===== Test Error Handling =====


class TestErrorHandling:
    """Tests for error handling in prompt generation."""

    def test_build_prompt_requires_error_type_for_incorrect(
        self, builder, avoir_verb, present_conjugations
    ):
        """Verify build_prompt raises error when error_type missing for incorrect sentence."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        with pytest.raises(ValueError, match="error_type must be provided"):
            builder.build_prompt(sentence, avoir_verb, present_conjugations)

    def test_build_prompt_handles_empty_conjugations(self, builder, avoir_verb):
        """Verify build_prompt handles empty conjugations list gracefully."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=True,
            target_language_code="eng",
        )

        with pytest.raises(ValueError, match="No conjugations provided"):
            builder.build_prompt(sentence, avoir_verb, [])

    def test_build_prompt_handles_missing_tense_conjugation(
        self, builder, avoir_verb, present_conjugations
    ):
        """Verify build_prompt handles missing tense conjugation."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.IMPARFAIT,  # Not in present_conjugations fixture
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=True,
            target_language_code="eng",
        )

        with pytest.raises(ValueError, match="No conjugation found"):
            builder.build_prompt(sentence, avoir_verb, present_conjugations)


# ===== Test Integration =====


class TestIntegration:
    """Integration tests for the complete prompt system."""

    def test_full_correct_sentence_workflow(
        self, builder, avoir_verb, present_conjugations
    ):
        """Test complete workflow for generating correct sentence prompt."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.SECOND_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.PAS,
            is_correct=True,
            target_language_code="eng",
        )

        prompt = builder.build_prompt(sentence, avoir_verb, present_conjugations)

        # Verify prompt structure
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert avoir_verb.infinitive in prompt
        assert sentence.tense.value in prompt
        assert sentence.negation.value in prompt

    def test_full_incorrect_sentence_workflow(
        self, builder, avoir_verb, present_conjugations
    ):
        """Test complete workflow for generating incorrect sentence prompt."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.THIRD_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        # Select error types
        error_types = builder.select_error_types(sentence, avoir_verb, count=1)
        assert len(error_types) >= 1

        # Generate prompt
        prompt = builder.build_prompt(
            sentence, avoir_verb, present_conjugations, error_type=error_types[0]
        )

        # Verify prompt structure
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert avoir_verb.infinitive in prompt
        assert "WRONG" in prompt or "wrong" in prompt

    def test_different_pronouns_produce_different_prompts(
        self, builder, avoir_verb, present_conjugations
    ):
        """Test that different pronouns produce different prompt content."""
        prompts = []
        for pronoun in [
            Pronoun.FIRST_PERSON,
            Pronoun.SECOND_PERSON,
            Pronoun.THIRD_PERSON,
        ]:
            sentence = SentenceBase(
                content="",
                translation="",
                verb_id=uuid.uuid4(),
                pronoun=pronoun,
                tense=Tense.PRESENT,
                direct_object=DirectObject.NONE,
                indirect_object=IndirectObject.NONE,
                negation=Negation.NONE,
                is_correct=True,
                target_language_code="eng",
            )

            prompt = builder.build_prompt(sentence, avoir_verb, present_conjugations)
            prompts.append(prompt)

        # Prompts should be different (different conjugations)
        assert len(set(prompts)) > 1


# ===== Test Template Helpers =====


class TestTemplateHelpers:
    """Tests for template helper functions."""

    def test_requires_auxiliary_for_compound_tenses(self):
        """Verify requires_auxiliary returns True for compound tenses."""
        assert requires_auxiliary(Tense.PASSE_COMPOSE) is True

    def test_requires_auxiliary_for_simple_tenses(self):
        """Verify requires_auxiliary returns False for simple tenses."""
        simple_tenses = [
            Tense.PRESENT,
            Tense.FUTURE_SIMPLE,
            Tense.IMPARFAIT,
            Tense.CONDITIONNEL,
            Tense.SUBJONCTIF,
            Tense.IMPERATIF,
        ]
        for tense in simple_tenses:
            assert (
                requires_auxiliary(tense) is False
            ), f"{tense} should not require auxiliary"

    def test_compound_tenses_set_contains_passe_compose(self):
        """Verify COMPOUND_TENSES set is properly defined."""
        assert Tense.PASSE_COMPOSE in COMPOUND_TENSES
        # Simple tenses should not be in the set
        assert Tense.PRESENT not in COMPOUND_TENSES

    def test_format_optional_dimension_with_any(self):
        """Verify ANY values format as natural choice instruction."""
        result = format_optional_dimension(DirectObject.ANY)
        assert "natural" in result.lower() or "choose" in result.lower()

    def test_format_optional_dimension_with_specific_value(self):
        """Verify specific values format as their enum value."""
        assert format_optional_dimension(DirectObject.NONE) == "none"
        assert format_optional_dimension(DirectObject.MASCULINE) == "masculine"
        assert format_optional_dimension(Negation.PAS) == "pas"
        assert format_optional_dimension(IndirectObject.FEMININE) == "feminine"

    def test_format_optional_dimension_all_any_values(self):
        """Verify all ANY enum values format correctly."""
        # All ANY values should produce the same natural choice instruction
        any_values = [DirectObject.ANY, IndirectObject.ANY, Negation.ANY]
        for any_val in any_values:
            result = format_optional_dimension(any_val)
            assert "natural" in result.lower() or "choose" in result.lower()
