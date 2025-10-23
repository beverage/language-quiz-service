"""Unit tests for VerbPromptGenerator.

Tests the three separate prompt generation methods:
1. generate_verb_properties_prompt() - for verb properties only
2. generate_conjugation_prompt() - for conjugations only
3. generate_objects_prompt() - for COD/COI analysis
"""

import pytest

from src.prompts.verb_prompts import VerbPromptGenerator


def test_generate_verb_properties_prompt_basic():
    """Test that verb properties prompt includes all required fields."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_verb_properties_prompt("parler", "eng")

    # Verify verb infinitive is included
    assert "parler" in prompt
    assert "eng" in prompt

    # Verify all required JSON fields are documented
    assert "auxiliary" in prompt
    assert "reflexive" in prompt
    assert "translation" in prompt
    assert "past_participle" in prompt
    assert "present_participle" in prompt
    assert "classification" in prompt
    assert "is_irregular" in prompt

    # Verify critical rules are included
    assert "CRITICAL RULES" in prompt
    assert "AUXILIARY DETERMINATION" in prompt
    assert "VERB GROUP CLASSIFICATION" in prompt


def test_generate_verb_properties_prompt_etre_avoir_special_cases():
    """Test that être/avoir special cases are documented in properties prompt."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_verb_properties_prompt("être", "eng")

    # Verify special cases for être/avoir are mentioned
    assert "CRITICAL SPECIAL CASES" in prompt
    assert "être" in prompt
    assert "avoir" in prompt
    assert "j'ai été" in prompt
    assert "j'ai eu" in prompt


def test_generate_verb_properties_prompt_dr_mrs_vandertramp():
    """Test that DR MRS VANDERTRAMP verbs are documented."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_verb_properties_prompt("aller", "eng")

    # Verify DR MRS VANDERTRAMP is mentioned
    assert "DR MRS VANDERTRAMP" in prompt
    assert "devenir" in prompt
    assert "aller" in prompt
    assert "mourir" in prompt


def test_generate_verb_properties_prompt_verb_groups():
    """Test that verb group classifications are documented."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_verb_properties_prompt("finir", "eng")

    # Verify all three groups are documented
    assert "first_group" in prompt
    assert "second_group" in prompt
    assert "third_group" in prompt

    # Verify -er verbs are mentioned
    assert "-er" in prompt
    assert "parler" in prompt

    # Verify -ir verbs with -issant pattern
    assert "-ir" in prompt
    assert "-issant" in prompt
    assert "finir" in prompt


def test_generate_conjugation_prompt_basic():
    """Test that conjugation prompt includes all 7 tenses."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_conjugation_prompt("parler", "avoir", False)

    # Verify verb and auxiliary are included
    assert "parler" in prompt
    assert "avoir" in prompt

    # Verify all 7 tenses are listed
    assert "present" in prompt
    assert "passe_compose" in prompt
    assert "imparfait" in prompt
    assert "future_simple" in prompt
    assert "conditionnel" in prompt
    assert "subjonctif" in prompt
    assert "imperatif" in prompt

    # Verify it's requesting a JSON array
    assert "[" in prompt
    assert "]" in prompt


def test_generate_conjugation_prompt_non_reflexive():
    """Test conjugation prompt for non-reflexive verb."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_conjugation_prompt("manger", "avoir", False)

    # Verify verb name is included
    assert "manger" in prompt

    # Verify reflexive is false in the example
    assert "false" in prompt.lower()

    # Should NOT mention reflexive verb in description
    assert "(reflexive verb)" not in prompt


def test_generate_conjugation_prompt_reflexive():
    """Test conjugation prompt for reflexive verbs."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_conjugation_prompt("laver", "être", True)

    # Verify verb name is included
    assert "laver" in prompt
    assert "être" in prompt

    # Verify reflexive note is added
    assert "(reflexive verb)" in prompt

    # Verify instructions for reflexive pronouns
    assert "reflexive pronoun" in prompt
    assert "me lave" in prompt or "me laves" in prompt


def test_generate_conjugation_prompt_critical_rules():
    """Test that critical rules are included in conjugation prompt."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_conjugation_prompt("parler", "avoir", False)

    # Verify critical rules
    assert "CRITICAL RULES" in prompt
    assert "ALL 7 tenses" in prompt
    assert "Do NOT include the pronoun" in prompt
    assert "EXACTLY the tense names" in prompt


def test_generate_objects_prompt_basic():
    """Test COD/COI prompt generation."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_objects_prompt("manger", "avoir")

    # Verify verb and auxiliary are included
    assert "manger" in prompt
    assert "avoir" in prompt

    # Verify JSON structure is documented
    assert "can_have_cod" in prompt
    assert "can_have_coi" in prompt

    # Verify definitions are provided
    assert "DEFINITIONS" in prompt or "COD:" in prompt
    assert "COI:" in prompt


def test_generate_objects_prompt_definitions():
    """Test that COD/COI definitions are clear."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_objects_prompt("donner", "avoir")

    # Verify COD definition
    assert "Direct object" in prompt or "NO preposition" in prompt
    assert "quelque chose" in prompt or "quelqu'un" in prompt

    # Verify COI definition
    assert "Indirect object" in prompt or "preposition" in prompt
    assert "à/de" in prompt


def test_generate_objects_prompt_examples():
    """Test that COD/COI examples are provided."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_objects_prompt("parler", "avoir")

    # Verify examples for different categories
    assert "COD ONLY" in prompt
    assert "COI ONLY" in prompt
    assert "BOTH COD AND COI" in prompt or "BOTH" in prompt
    assert "NEITHER" in prompt


def test_generate_objects_prompt_dr_mrs_vandertramp():
    """Test that DR MRS VANDERTRAMP is mentioned for context."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_objects_prompt("sortir", "avoir")

    # DR MRS VANDERTRAMP should be mentioned for être/avoir transitivity
    assert "DR MRS VANDERTRAMP" in prompt or "sortir" in prompt


def test_generate_objects_prompt_reflexive_verbs():
    """Test that reflexive verbs are mentioned in COD/COI prompt."""
    generator = VerbPromptGenerator()
    prompt = generator.generate_objects_prompt("laver", "être")

    # Verify reflexive verbs are addressed
    assert "reflexive" in prompt.lower() or "se laver" in prompt


def test_generate_verb_prompt_deprecated_logs_warning(caplog):
    """Test that deprecated generate_verb_prompt logs warning."""
    import logging

    caplog.set_level(logging.WARNING)

    generator = VerbPromptGenerator()
    prompt = generator.generate_verb_prompt("parler")

    # Should log deprecation warning
    assert "deprecated" in caplog.text.lower()

    # Should still return a valid prompt (backward compatibility)
    assert "parler" in prompt
    assert len(prompt) > 100


def test_generate_verb_prompt_deprecated_returns_properties_prompt():
    """Test that deprecated method returns properties prompt."""
    generator = VerbPromptGenerator()

    # Get both prompts
    deprecated_prompt = generator.generate_verb_prompt(
        "être", "eng", include_tenses=False
    )
    properties_prompt = generator.generate_verb_properties_prompt("être", "eng")

    # They should be identical (deprecated calls properties internally)
    assert deprecated_prompt == properties_prompt


def test_prompt_generator_instance_creation():
    """Test that VerbPromptGenerator can be instantiated."""
    generator = VerbPromptGenerator()
    assert generator is not None

    # All three main methods should be callable
    assert callable(generator.generate_verb_properties_prompt)
    assert callable(generator.generate_conjugation_prompt)
    assert callable(generator.generate_objects_prompt)
