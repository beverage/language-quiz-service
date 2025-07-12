"""Unit tests for Pydantic sentence schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.sentences import (
    SentenceCreate,
    SentenceUpdate,
    Pronoun,
    Negation,
)


@pytest.mark.unit
class TestSentenceCreate:
    """Test cases for the SentenceCreate schema."""

    def test_valid_sentence_creation(self, sample_sentence_data: dict):
        """Tests that a valid SentenceCreate model can be created."""
        sentence = SentenceCreate(**sample_sentence_data)
        assert sentence.content == sample_sentence_data["content"]
        assert sentence.pronoun == Pronoun.FIRST_PERSON

    @pytest.mark.parametrize("field_to_remove", ["content", "translation", "verb_id"])
    def test_missing_required_fields_fail(
        self, field_to_remove: str, sample_sentence_data: dict
    ):
        """Tests that missing required fields raise a validation error."""
        invalid_data = sample_sentence_data.copy()
        del invalid_data[field_to_remove]
        with pytest.raises(ValidationError):
            SentenceCreate(**invalid_data)

    def test_enum_value_validation(self, sample_sentence_data: dict):
        """Tests that invalid enum values raise a validation error."""
        invalid_data = sample_sentence_data.copy()
        invalid_data["pronoun"] = "invalid_pronoun"
        with pytest.raises(ValidationError):
            SentenceCreate(**invalid_data)


@pytest.mark.unit
class TestSentenceUpdate:
    """Test cases for the SentenceUpdate schema."""

    def test_valid_partial_update(self):
        """Tests that a valid partial update can be performed."""
        update_data = {"content": "Je ne parle pas.", "negation": Negation.PAS}
        sentence_update = SentenceUpdate(**update_data)
        assert sentence_update.content == "Je ne parle pas."
        assert sentence_update.negation == Negation.PAS
        assert sentence_update.translation is None

    def test_update_with_no_fields(self):
        """Tests that an update with no fields is valid."""
        sentence_update = SentenceUpdate()
        assert sentence_update.model_dump(exclude_unset=True) == {}
