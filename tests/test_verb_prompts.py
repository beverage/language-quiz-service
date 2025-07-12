"""Unit tests for verb prompt generation."""

import pytest

from src.prompts.verb_prompts import VerbPromptGenerator


@pytest.mark.unit
class TestVerbPromptGenerator:
    """Test cases for the VerbPromptGenerator."""

    def test_generate_verb_prompt(self):
        """Tests that the verb prompt is generated correctly."""
        generator = VerbPromptGenerator()
        infinitive = "parler"
        prompt = generator.generate_verb_prompt(infinitive)

        assert f"verb {infinitive} in the following format" in prompt
        assert f'"infinitive": "{infinitive}"' in prompt
        assert "Return well-formed JSON" in prompt
