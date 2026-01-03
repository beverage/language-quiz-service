"""Unit tests for VerbPromptGenerator.

Tests focus on behavioral contracts rather than prompt text content.
Prompt effectiveness is validated by LLM output quality, not string matching.
"""

import logging

from src.prompts.verb_prompts import VerbPromptGenerator


def test_generate_verb_prompt_deprecated_logs_warning(caplog):
    """Test that deprecated generate_verb_prompt logs warning."""
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
