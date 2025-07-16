"""Unit tests for Pydantic sentence schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.sentences import (
    Negation,
    SentenceCreate,
    SentenceUpdate,
)
from tests.sentences.fixtures import generate_random_sentence_data


@pytest.mark.unit
class TestSentenceCreate:
    """Test cases for the SentenceCreate schema."""

    @pytest.fixture
    def sample_sentence_data(self):
        """Provide sample sentence data dictionary for testing."""
        return generate_random_sentence_data()

    def test_valid_sentence_creation(self, sample_sentence_data: dict):
        """Tests that a valid SentenceCreate model can be created."""
        sentence = SentenceCreate(**sample_sentence_data)
        assert sentence.content == sample_sentence_data["content"]
        assert sentence.pronoun.value == sample_sentence_data["pronoun"]

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

    @pytest.mark.parametrize(
        "invalid_code", ["en", "english", "e", "", "1234", "fr-FR"]
    )
    def test_invalid_language_code_validation(
        self, invalid_code: str, sample_sentence_data: dict
    ):
        """Tests that invalid language codes raise a validation error."""
        invalid_data = sample_sentence_data.copy()
        invalid_data["target_language_code"] = invalid_code
        with pytest.raises(ValidationError) as exc_info:
            SentenceCreate(**invalid_data)
        error_message = str(exc_info.value)
        assert (
            "Language code cannot be empty" in error_message
            or "Language code must be 3 characters" in error_message
        )

    @pytest.mark.parametrize("valid_code", ["eng", "fra", "spa", "deu", "ENG", "Fra"])
    def test_valid_language_code_validation(
        self, valid_code: str, sample_sentence_data: dict
    ):
        """Tests that valid language codes are accepted and normalized to lowercase."""
        valid_data = sample_sentence_data.copy()
        valid_data["target_language_code"] = valid_code
        sentence = SentenceCreate(**valid_data)
        assert sentence.target_language_code == valid_code.lower()


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

    @pytest.mark.parametrize(
        "invalid_code", ["en", "english", "e", "", "1234", "fr-FR"]
    )
    def test_invalid_language_code_validation_update(self, invalid_code: str):
        """Tests that invalid language codes raise a validation error in updates."""
        with pytest.raises(ValidationError) as exc_info:
            SentenceUpdate(target_language_code=invalid_code)
        error_message = str(exc_info.value)
        assert (
            "Language code cannot be empty" in error_message
            or "Language code must be 3 characters" in error_message
        )

    @pytest.mark.parametrize("valid_code", ["eng", "fra", "spa", "deu", "ENG", "Fra"])
    def test_valid_language_code_validation_update(self, valid_code: str):
        """Tests that valid language codes are accepted and normalized in updates."""
        sentence_update = SentenceUpdate(target_language_code=valid_code)
        assert sentence_update.target_language_code == valid_code.lower()
