"""Tests for tense-specific hints in templates.py"""

import uuid
from datetime import datetime

import pytest

from src.prompts.sentences.templates import (
    TENSE_HINTS,
    build_base_template,
    get_tense_hint,
)
from src.schemas.verbs import AuxiliaryType, Tense, Verb


@pytest.fixture
def sample_verb():
    """Create a sample verb for testing."""
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


class TestTenseHints:
    """Tests for tense-specific hints."""

    def test_all_tenses_have_hints(self):
        """Verify all defined tenses have hints."""
        expected_tenses = [
            Tense.PRESENT,
            Tense.PASSE_COMPOSE,
            Tense.PLUS_QUE_PARFAIT,
            Tense.IMPARFAIT,
            Tense.FUTURE_SIMPLE,
            Tense.CONDITIONNEL,
            Tense.SUBJONCTIF,
            Tense.IMPERATIF,
        ]
        for tense in expected_tenses:
            assert tense in TENSE_HINTS, f"Missing hint for {tense}"
            assert len(TENSE_HINTS[tense]) > 0, f"Empty hint for {tense}"

    def test_get_tense_hint_returns_string(self):
        """Verify get_tense_hint returns strings for known tenses."""
        for tense in TENSE_HINTS:
            hint = get_tense_hint(tense)
            assert isinstance(hint, str)
            assert len(hint) > 20  # Should be substantive

    def test_get_tense_hint_returns_none_for_unknown(self):
        """Verify get_tense_hint returns None for undefined tenses."""
        # Create a mock tense value that's not in hints
        # Since all our tenses have hints, this tests the fallback behavior
        result = get_tense_hint(None)  # type: ignore
        assert result is None

    def test_subjonctif_hint_discourages_il_faut_que(self):
        """Verify subjunctive hint explicitly discourages overuse of 'il faut que'."""
        hint = TENSE_HINTS[Tense.SUBJONCTIF]
        assert "il faut que" in hint.lower()
        assert "not always" in hint.lower() or "do not always" in hint.lower()

    def test_subjonctif_hint_provides_alternatives(self):
        """Verify subjunctive hint provides alternative triggers."""
        hint = TENSE_HINTS[Tense.SUBJONCTIF]
        alternatives = ["je veux que", "bien que", "pour que", "avant que"]
        found = sum(1 for alt in alternatives if alt in hint.lower())
        assert found >= 3, "Should provide at least 3 alternative subjunctive triggers"

    def test_passe_compose_hint_mentions_time_markers(self):
        """Verify passé composé hint suggests time markers."""
        hint = TENSE_HINTS[Tense.PASSE_COMPOSE]
        time_markers = ["hier", "semaine dernière", "ce matin"]
        found = sum(1 for marker in time_markers if marker in hint.lower())
        assert found >= 2, "Should mention time markers for passé composé"

    def test_conditionnel_hint_varies_construction(self):
        """Verify conditional hint encourages variety."""
        hint = TENSE_HINTS[Tense.CONDITIONNEL]
        assert "vary" in hint.lower() or "avoid always" in hint.lower()


class TestBuildBaseTemplateWithHints:
    """Tests for base template including tense hints."""

    def test_base_template_includes_style_hint(self, sample_verb):
        """Verify base template includes STYLE HINT section."""
        template = build_base_template(sample_verb, Tense.PRESENT)
        assert "STYLE HINT:" in template

    def test_base_template_includes_tense_specific_content(self, sample_verb):
        """Verify template includes content from the tense hint."""
        template = build_base_template(sample_verb, Tense.SUBJONCTIF)
        # Should contain some of the subjunctive hint content
        assert "subjunctive" in template.lower() or "je veux que" in template.lower()

    def test_different_tenses_produce_different_hints(self, sample_verb):
        """Verify different tenses produce different style hints."""
        present_template = build_base_template(sample_verb, Tense.PRESENT)
        subjonctif_template = build_base_template(sample_verb, Tense.SUBJONCTIF)
        passe_compose_template = build_base_template(sample_verb, Tense.PASSE_COMPOSE)

        # Extract just the hint sections for comparison
        templates = [present_template, subjonctif_template, passe_compose_template]
        assert len(set(templates)) == 3, "Each tense should produce unique template"

    def test_compound_tense_includes_auxiliary_and_hint(self, sample_verb):
        """Verify compound tenses include both auxiliary info and style hint."""
        template = build_base_template(sample_verb, Tense.PASSE_COMPOSE)

        # Should have auxiliary info
        assert "Past Participle:" in template
        assert "Auxiliary:" in template

        # Should also have style hint
        assert "STYLE HINT:" in template
        assert "hier" in template.lower() or "semaine" in template.lower()

    def test_simple_tense_excludes_auxiliary_includes_hint(self, sample_verb):
        """Verify simple tenses exclude auxiliary but include style hint."""
        template = build_base_template(sample_verb, Tense.PRESENT)

        # Should NOT have auxiliary info
        assert "Past Participle:" not in template
        assert "Auxiliary:" not in template

        # Should have style hint
        assert "STYLE HINT:" in template
