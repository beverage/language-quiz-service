"""Test suite for pronoun substitution prompt system.

Tests the pronoun prompt generation system for object pronoun (COD/COI) problems.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.prompts.sentences import ErrorType, SentencePromptBuilder
from src.prompts.sentences.pronoun_prompt import (
    PRONOUN_ERROR_BUILDERS,
    build_correct_pronoun_prompt,
    build_pronoun_error_prompt,
    build_wrong_category_prompt,
    build_wrong_gender_prompt,
    build_wrong_number_prompt,
    build_wrong_order_prompt,
    build_wrong_placement_prompt,
)
from src.schemas.problems import GrammarFocus
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
        infinitive="donner",
        translation="to give",
        past_participle="donné",
        present_participle="donnant",
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
        infinitive="partir",
        translation="to leave",
        past_participle="parti",
        present_participle="partant",
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
    conjugation.first_person_singular = "donne"
    conjugation.second_person_singular = "donnes"
    conjugation.third_person_singular = "donne"
    conjugation.first_person_plural = "donnons"
    conjugation.second_person_plural = "donnez"
    conjugation.third_person_plural = "donnent"
    return [conjugation]


@pytest.fixture
def passe_compose_conjugations():
    """Create mock passé composé conjugations."""
    conjugation = MagicMock()
    conjugation.tense = Tense.PASSE_COMPOSE
    conjugation.first_person_singular = "ai donné"
    conjugation.second_person_singular = "as donné"
    conjugation.third_person_singular = "a donné"
    conjugation.first_person_plural = "avons donné"
    conjugation.second_person_plural = "avez donné"
    conjugation.third_person_plural = "ont donné"
    return [conjugation]


@pytest.fixture
def cod_sentence():
    """Create a sentence with COD pronoun (le)."""
    return SentenceBase(
        content="",
        translation="",
        verb_id=uuid.uuid4(),
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.MASCULINE,
        indirect_object=IndirectObject.NONE,
        negation=Negation.NONE,
        is_correct=True,
        target_language_code="eng",
    )


@pytest.fixture
def coi_sentence():
    """Create a sentence with COI pronoun (lui)."""
    return SentenceBase(
        content="",
        translation="",
        verb_id=uuid.uuid4(),
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.NONE,
        indirect_object=IndirectObject.MASCULINE,
        negation=Negation.NONE,
        is_correct=True,
        target_language_code="eng",
    )


@pytest.fixture
def double_pronoun_sentence():
    """Create a sentence with both COD and COI pronouns."""
    return SentenceBase(
        content="",
        translation="",
        verb_id=uuid.uuid4(),
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.MASCULINE,
        indirect_object=IndirectObject.FEMININE,
        negation=Negation.NONE,
        is_correct=True,
        target_language_code="eng",
    )


# ===== Test Derived Properties =====


class TestDerivedProperties:
    """Tests for SentenceBase derived properties."""

    def test_has_pronoun_substitution_with_cod(self, cod_sentence):
        """Verify has_pronoun_substitution is True with COD."""
        assert cod_sentence.has_pronoun_substitution is True

    def test_has_pronoun_substitution_with_coi(self, coi_sentence):
        """Verify has_pronoun_substitution is True with COI."""
        assert coi_sentence.has_pronoun_substitution is True

    def test_has_pronoun_substitution_with_neither(self):
        """Verify has_pronoun_substitution is False with no objects."""
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
        assert sentence.has_pronoun_substitution is False

    def test_has_pronoun_substitution_with_any(self):
        """Verify has_pronoun_substitution is False with ANY (not specific)."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.ANY,
            indirect_object=IndirectObject.ANY,
            negation=Negation.NONE,
            is_correct=True,
            target_language_code="eng",
        )
        assert sentence.has_pronoun_substitution is False

    def test_has_double_pronouns_true(self, double_pronoun_sentence):
        """Verify has_double_pronouns is True with both COD and COI."""
        assert double_pronoun_sentence.has_double_pronouns is True

    def test_has_double_pronouns_false_cod_only(self, cod_sentence):
        """Verify has_double_pronouns is False with only COD."""
        assert cod_sentence.has_double_pronouns is False

    def test_has_double_pronouns_false_coi_only(self, coi_sentence):
        """Verify has_double_pronouns is False with only COI."""
        assert coi_sentence.has_double_pronouns is False


# ===== Test Correct Pronoun Prompts =====


class TestCorrectPronounPrompts:
    """Tests for correct pronoun sentence prompt generation."""

    def test_correct_prompt_contains_verb_info(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct pronoun prompt contains verb information."""
        prompt = build_correct_pronoun_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        assert avoir_verb.infinitive in prompt

    def test_correct_prompt_contains_pronoun_rules(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct pronoun prompt contains pronoun placement rules."""
        prompt = build_correct_pronoun_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        assert "PRONOUN" in prompt.upper()
        assert "BEFORE" in prompt.upper() or "before" in prompt

    def test_correct_prompt_mentions_cod_pronoun(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct pronoun prompt mentions the COD pronoun."""
        prompt = build_correct_pronoun_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        # Should mention le (masculine COD)
        assert "le" in prompt.lower() or "COD" in prompt

    def test_correct_prompt_mentions_coi_pronoun(
        self, coi_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct pronoun prompt mentions the COI pronoun."""
        prompt = build_correct_pronoun_prompt(
            coi_sentence, avoir_verb, present_conjugations
        )

        # Should mention lui (COI)
        assert "lui" in prompt.lower() or "COI" in prompt

    def test_correct_prompt_handles_double_pronouns(
        self, double_pronoun_sentence, avoir_verb, present_conjugations
    ):
        """Verify correct pronoun prompt handles double pronouns."""
        prompt = build_correct_pronoun_prompt(
            double_pronoun_sentence, avoir_verb, present_conjugations
        )

        # Should mention both pronouns and ordering
        assert "COD" in prompt or "le" in prompt.lower()
        assert "COI" in prompt or "lui" in prompt.lower()
        assert "DOUBLE" in prompt.upper() or "order" in prompt.lower()


# ===== Test Error Prompt Builders =====


class TestWrongPlacementPrompt:
    """Tests for wrong placement error prompt generation."""

    def test_wrong_placement_prompt_mentions_wrong_position(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify wrong placement prompt specifies wrong position."""
        cod_sentence.is_correct = False
        prompt = build_wrong_placement_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        assert "WRONG" in prompt.upper()
        assert "position" in prompt.lower() or "AFTER" in prompt.upper()

    def test_wrong_placement_prompt_contains_explanation_instruction(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify wrong placement prompt includes explanation instruction."""
        cod_sentence.is_correct = False
        prompt = build_wrong_placement_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        assert "explanation" in prompt.lower() or "EXPLANATION" in prompt


class TestWrongOrderPrompt:
    """Tests for wrong order error prompt generation."""

    def test_wrong_order_prompt_mentions_order(
        self, double_pronoun_sentence, avoir_verb, present_conjugations
    ):
        """Verify wrong order prompt specifies order error."""
        double_pronoun_sentence.is_correct = False
        prompt = build_wrong_order_prompt(
            double_pronoun_sentence, avoir_verb, present_conjugations
        )

        assert "order" in prompt.lower() or "ORDER" in prompt

    def test_wrong_order_prompt_specifies_wrong_sequence(
        self, double_pronoun_sentence, avoir_verb, present_conjugations
    ):
        """Verify wrong order prompt specifies the wrong sequence."""
        double_pronoun_sentence.is_correct = False
        prompt = build_wrong_order_prompt(
            double_pronoun_sentence, avoir_verb, present_conjugations
        )

        # Should mention COD before COI is correct
        assert "COD" in prompt and "COI" in prompt


class TestWrongCategoryPrompt:
    """Tests for wrong category error prompt generation."""

    def test_wrong_category_prompt_specifies_category_mismatch(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify wrong category prompt specifies COD/COI confusion."""
        cod_sentence.is_correct = False
        prompt = build_wrong_category_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        assert "COD" in prompt or "COI" in prompt
        assert "WRONG" in prompt.upper()


class TestWrongGenderPrompt:
    """Tests for wrong gender error prompt generation."""

    def test_wrong_gender_prompt_specifies_gender_mismatch(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify wrong gender prompt specifies gender mismatch."""
        cod_sentence.is_correct = False
        prompt = build_wrong_gender_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        assert "gender" in prompt.lower() or "GENDER" in prompt


class TestWrongNumberPrompt:
    """Tests for wrong number error prompt generation."""

    def test_wrong_number_prompt_specifies_number_mismatch(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify wrong number prompt specifies number mismatch."""
        cod_sentence.is_correct = False
        prompt = build_wrong_number_prompt(
            cod_sentence, avoir_verb, present_conjugations
        )

        assert "number" in prompt.lower() or "NUMBER" in prompt
        assert "singular" in prompt.lower() or "plural" in prompt.lower()


# ===== Test Error Builder Routing =====


class TestPronounErrorBuilderRouting:
    """Tests for pronoun error builder routing."""

    def test_pronoun_error_builders_map_contains_all_pronoun_errors(self):
        """Verify PRONOUN_ERROR_BUILDERS contains all pronoun error types."""
        pronoun_error_types = {
            ErrorType.WRONG_PLACEMENT,
            ErrorType.WRONG_ORDER,
            ErrorType.WRONG_CATEGORY,
            ErrorType.WRONG_GENDER,
            ErrorType.WRONG_NUMBER,
        }

        for error_type in pronoun_error_types:
            assert error_type in PRONOUN_ERROR_BUILDERS

    def test_build_pronoun_error_prompt_routes_correctly(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify build_pronoun_error_prompt routes to correct builder."""
        cod_sentence.is_correct = False

        for error_type in PRONOUN_ERROR_BUILDERS:
            prompt = build_pronoun_error_prompt(
                cod_sentence, avoir_verb, present_conjugations, error_type
            )
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_build_pronoun_error_prompt_rejects_conjugation_errors(
        self, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify build_pronoun_error_prompt rejects non-pronoun errors."""
        cod_sentence.is_correct = False

        with pytest.raises(ValueError, match="Unknown pronoun error type"):
            build_pronoun_error_prompt(
                cod_sentence,
                avoir_verb,
                present_conjugations,
                ErrorType.WRONG_CONJUGATION,
            )


# ===== Test Builder Integration with Focus =====


class TestBuilderWithFocus:
    """Tests for SentencePromptBuilder with focus parameter."""

    def test_select_error_types_conjugation_focus(self, builder, avoir_verb):
        """Verify select_error_types returns conjugation errors for conjugation focus."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.MASCULINE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        error_types = builder.select_error_types(
            sentence, avoir_verb, focus=GrammarFocus.CONJUGATION, count=3
        )

        # Should only include conjugation errors
        assert all(
            et in {ErrorType.WRONG_CONJUGATION, ErrorType.WRONG_AUXILIARY}
            for et in error_types
        )

    def test_select_error_types_pronouns_focus(self, builder, avoir_verb):
        """Verify select_error_types returns pronoun errors for pronouns focus."""
        sentence = SentenceBase(
            content="",
            translation="",
            verb_id=uuid.uuid4(),
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.MASCULINE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=False,
            target_language_code="eng",
        )

        error_types = builder.select_error_types(
            sentence, avoir_verb, focus=GrammarFocus.PRONOUNS, count=3
        )

        # Should only include pronoun errors
        pronoun_errors = {
            ErrorType.WRONG_PLACEMENT,
            ErrorType.WRONG_ORDER,
            ErrorType.WRONG_CATEGORY,
            ErrorType.WRONG_GENDER,
            ErrorType.WRONG_NUMBER,
        }
        assert all(et in pronoun_errors for et in error_types)

    def test_select_error_types_includes_wrong_order_for_double_pronouns(
        self, builder, avoir_verb, double_pronoun_sentence
    ):
        """Verify WRONG_ORDER is included when double pronouns present."""
        double_pronoun_sentence.is_correct = False

        # Run multiple times to see if WRONG_ORDER appears
        all_error_types = set()
        for _ in range(10):
            error_types = builder.select_error_types(
                double_pronoun_sentence,
                avoir_verb,
                focus=GrammarFocus.PRONOUNS,
                count=5,
            )
            all_error_types.update(error_types)

        assert ErrorType.WRONG_ORDER in all_error_types

    def test_select_error_types_excludes_wrong_order_for_single_pronoun(
        self, builder, avoir_verb, cod_sentence
    ):
        """Verify WRONG_ORDER is excluded when only single pronoun."""
        cod_sentence.is_correct = False

        # Check multiple times
        for _ in range(10):
            error_types = builder.select_error_types(
                cod_sentence, avoir_verb, focus=GrammarFocus.PRONOUNS, count=5
            )
            assert ErrorType.WRONG_ORDER not in error_types

    def test_build_prompt_uses_pronoun_prompt_for_correct_with_pronoun_focus(
        self, builder, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify build_prompt uses pronoun prompt for correct sentence with pronouns focus."""
        prompt = builder.build_prompt(
            cod_sentence,
            avoir_verb,
            present_conjugations,
            focus=GrammarFocus.PRONOUNS,
        )

        # Should contain pronoun-specific content
        assert "PRONOUN" in prompt.upper() or "pronoun" in prompt

    def test_build_prompt_uses_pronoun_error_prompt_for_incorrect_with_pronoun_focus(
        self, builder, cod_sentence, avoir_verb, present_conjugations
    ):
        """Verify build_prompt uses pronoun error prompt for incorrect sentence with pronouns focus."""
        cod_sentence.is_correct = False

        prompt = builder.build_prompt(
            cod_sentence,
            avoir_verb,
            present_conjugations,
            error_type=ErrorType.WRONG_PLACEMENT,
            focus=GrammarFocus.PRONOUNS,
        )

        # Should contain placement error content
        assert "WRONG" in prompt.upper()
        assert "position" in prompt.lower() or "AFTER" in prompt.upper()


# ===== Test GrammarFocus Enum =====


class TestGrammarFocusEnum:
    """Tests for GrammarFocus enum."""

    def test_grammar_focus_values(self):
        """Verify GrammarFocus enum has expected values."""
        assert GrammarFocus.CONJUGATION.value == "conjugation"
        assert GrammarFocus.PRONOUNS.value == "pronouns"

    def test_grammar_focus_is_string_enum(self):
        """Verify GrammarFocus is a string enum."""
        assert str(GrammarFocus.CONJUGATION) == "GrammarFocus.CONJUGATION"
        assert GrammarFocus.CONJUGATION.value == "conjugation"
