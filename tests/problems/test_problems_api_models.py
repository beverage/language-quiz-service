"""Unit tests for Problem API models."""

import pytest
from pydantic import ValidationError

from src.api.models.problems import ProblemRandomRequest
from src.schemas.problems import GrammarProblemConstraints


@pytest.mark.unit
class TestProblemRandomRequest:
    """Test cases for ProblemRandomRequest API model with topic_tags."""

    def test_default_values(self):
        """Test that ProblemRandomRequest has correct default values."""
        request = ProblemRandomRequest()
        assert request.constraints is None
        assert request.statement_count == 4
        assert request.target_language_code == "eng"
        assert request.topic_tags == []

    def test_topic_tags_accepts_list(self):
        """Test that topic_tags accepts a list of strings."""
        request = ProblemRandomRequest(topic_tags=["test", "grammar", "advanced"])
        assert request.topic_tags == ["test", "grammar", "advanced"]
        assert len(request.topic_tags) == 3

    def test_topic_tags_empty_list_valid(self):
        """Test that empty topic_tags list is valid."""
        request = ProblemRandomRequest(topic_tags=[])
        assert request.topic_tags == []

    def test_topic_tags_defaults_to_empty_list(self):
        """Test that topic_tags defaults to empty list when omitted."""
        request = ProblemRandomRequest(statement_count=5)
        assert isinstance(request.topic_tags, list)
        assert len(request.topic_tags) == 0

    def test_topic_tags_with_constraints(self):
        """Test that topic_tags work alongside other parameters."""
        constraints = GrammarProblemConstraints(
            grammatical_focus=["negation"], includes_negation=True
        )
        request = ProblemRandomRequest(
            constraints=constraints,
            statement_count=6,
            target_language_code="fra",
            topic_tags=["test_data", "negation_focus"],
        )
        assert request.topic_tags == ["test_data", "negation_focus"]
        assert request.statement_count == 6
        assert request.target_language_code == "fra"
        assert request.constraints.includes_negation is True

    def test_topic_tags_with_duplicate_values(self):
        """Test that duplicate tags are preserved (no automatic deduplication)."""
        request = ProblemRandomRequest(topic_tags=["grammar", "grammar", "test"])
        # Pydantic doesn't deduplicate by default - this is fine
        assert request.topic_tags == ["grammar", "grammar", "test"]

    def test_topic_tags_with_special_characters(self):
        """Test that topic_tags handle special characters."""
        request = ProblemRandomRequest(
            topic_tags=["test-data", "tag_with_underscore", "tag.with.dots"]
        )
        assert len(request.topic_tags) == 3
        assert "test-data" in request.topic_tags

    @pytest.mark.parametrize(
        "invalid_tags",
        [
            "not_a_list",  # String instead of list
            123,  # Number instead of list
            {"tag": "value"},  # Dict instead of list
        ],
    )
    def test_topic_tags_invalid_types_rejected(self, invalid_tags):
        """Test that non-list types for topic_tags are rejected."""
        with pytest.raises(ValidationError):
            ProblemRandomRequest(topic_tags=invalid_tags)

    def test_statement_count_validation_with_tags(self):
        """Test statement_count validation works alongside topic_tags."""
        # Valid counts
        request = ProblemRandomRequest(statement_count=2, topic_tags=["test"])
        assert request.statement_count == 2

        request = ProblemRandomRequest(statement_count=6, topic_tags=["test"])
        assert request.statement_count == 6

        # Invalid counts
        with pytest.raises(ValidationError):
            ProblemRandomRequest(statement_count=1, topic_tags=["test"])  # Too few

        with pytest.raises(ValidationError):
            ProblemRandomRequest(statement_count=7, topic_tags=["test"])  # Too many

    def test_complete_request_with_all_fields(self):
        """Test ProblemRandomRequest with all fields populated."""
        constraints = GrammarProblemConstraints(
            grammatical_focus=["direct_objects", "negation"],
            verb_infinitives=["manger", "parler"],
            tenses_used=["present", "passe_compose"],
            includes_negation=True,
            includes_cod=True,
            includes_coi=False,
        )
        request = ProblemRandomRequest(
            constraints=constraints,
            statement_count=5,
            target_language_code="spa",
            topic_tags=["test_data", "custom_tag", "advanced_grammar"],
        )

        assert request.statement_count == 5
        assert request.target_language_code == "spa"
        assert len(request.topic_tags) == 3
        assert "test_data" in request.topic_tags
        assert request.constraints.includes_negation is True
        assert len(request.constraints.verb_infinitives) == 2
