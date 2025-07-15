"""Unit tests for the verb prompt generator."""

import pytest

from src.prompts.verb_prompts import VerbPromptGenerator


@pytest.mark.unit
class TestVerbPromptGenerator:
    """Test suite for the VerbPromptGenerator."""

    def test_generate_verb_prompt(self):
        """Test generating a verb prompt."""
        generator = VerbPromptGenerator()
        verb_infinitive = "parler"
        prompt = generator.generate_verb_prompt(verb_infinitive)

        assert verb_infinitive in prompt
        assert "conjugation" in prompt
        assert "tenses" in prompt
