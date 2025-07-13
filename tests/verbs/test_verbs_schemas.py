"""Unit tests for Pydantic verb schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.verbs import (
    AuxiliaryType,
    VerbClassification,
    VerbCreate,
    VerbUpdate,
)


@pytest.mark.unit
class TestVerbCreate:
    """Test cases for the VerbCreate schema."""

    def test_valid_verb_creation(self, sample_verb_create: VerbCreate):
        """Tests that a valid VerbCreate model can be created."""
        assert sample_verb_create.infinitive == "parler"
        assert sample_verb_create.translation == "to speak"
        assert sample_verb_create.target_language_code == "eng"

    def test_field_normalization(self, sample_verb_data: dict):
        """Tests that fields are properly stripped of whitespace."""
        data = sample_verb_data.copy()
        data["infinitive"] = "  parler  "
        data["translation"] = "  to speak  "
        verb = VerbCreate(**data)
        assert verb.infinitive == "parler"
        assert verb.translation == "to speak"

    @pytest.mark.parametrize(
        "field, value",
        [
            ("infinitive", ""),
            ("infinitive", "  "),
            ("translation", ""),
            ("past_participle", ""),
            ("present_participle", ""),
        ],
    )
    def test_empty_text_fields_fail(
        self, field: str, value: str, sample_verb_data: dict
    ):
        """Tests that empty text fields raise a validation error."""
        invalid_data = sample_verb_data.copy()
        invalid_data[field] = value
        with pytest.raises(ValidationError):
            VerbCreate(**invalid_data)

    @pytest.mark.parametrize(
        "code, is_valid",
        [
            ("fra", True),
            ("eng", True),
            ("deu", True),
            ("es", False),
            ("french", False),
            ("123", False),
            ("", False),
        ],
    )
    def test_language_code_validation(
        self, code: str, is_valid: bool, sample_verb_data: dict
    ):
        """Tests language code validation for format and content."""
        data = sample_verb_data.copy()
        data["target_language_code"] = code
        if is_valid:
            verb = VerbCreate(**data)
            assert verb.target_language_code == code
        else:
            with pytest.raises(ValidationError):
                VerbCreate(**data)

    def test_auxiliary_type_values(self, sample_verb_data: dict):
        """Tests that only valid auxiliary types are accepted."""
        data = sample_verb_data.copy()
        data["auxiliary"] = "invalid_aux"
        with pytest.raises(ValidationError):
            VerbCreate(**data)

    def test_verb_classification_values(self, sample_verb_data: dict):
        """Tests that only valid verb classifications are accepted."""
        data = sample_verb_data.copy()
        data["classification"] = "invalid_class"
        with pytest.raises(ValidationError):
            VerbCreate(**data)


@pytest.mark.unit
class TestVerbUpdate:
    """Test cases for the VerbUpdate schema."""

    def test_valid_partial_update(self):
        """Tests that a valid partial update can be performed."""
        update_data = {"infinitive": "chanter", "reflexive": True}
        verb_update = VerbUpdate(**update_data)
        assert verb_update.infinitive == "chanter"
        assert verb_update.reflexive is True
        assert verb_update.translation is None

    def test_update_with_all_fields_none(self):
        """Tests that an update with no fields is valid."""
        verb_update = VerbUpdate()
        assert verb_update.model_dump(exclude_unset=True) == {}

    def test_empty_string_update_fails(self):
        """Tests that updating a field with an empty string fails."""
        with pytest.raises(ValidationError):
            VerbUpdate(infinitive="")

    def test_invalid_language_code_update_fails(self):
        """Tests that updating with an invalid language code fails."""
        with pytest.raises(ValidationError):
            VerbUpdate(target_language_code="12")


@pytest.mark.unit
class TestVerbEnums:
    """Test cases for verb-related enums."""

    def test_auxiliary_type_enum(self):
        """Tests the values of the AuxiliaryType enum."""
        assert AuxiliaryType.AVOIR == "avoir"
        assert AuxiliaryType.ETRE == "être"

    def test_verb_classification_enum(self):
        """Tests the values of the VerbClassification enum."""
        assert VerbClassification.FIRST_GROUP == "first_group"
        assert VerbClassification.SECOND_GROUP == "second_group"
        assert VerbClassification.THIRD_GROUP == "third_group"
