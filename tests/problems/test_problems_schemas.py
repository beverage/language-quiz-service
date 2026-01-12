"""Unit tests for Pydantic problem schemas."""

from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.api.models.problems import ProblemRandomRequest
from src.schemas.problems import (
    DifficultyLevel,
    GrammarFocus,
    GrammarProblemConstraints,
    Problem,
    ProblemBase,
    ProblemCreate,
    ProblemFilters,
    ProblemSearchRequest,
    ProblemSearchResponse,
    ProblemSummary,
    ProblemType,
    ProblemUpdate,
    ProblemWithMetadata,
)


@pytest.fixture
def sample_grammar_statements() -> list[dict[str, Any]]:
    """Sample grammar problem statements."""
    return [
        {
            "content": "Je mange une pomme.",
            "is_correct": True,
            "translation": "I eat an apple.",
        },
        {
            "content": "Je mange un pomme.",
            "is_correct": False,
            "explanation": "Incorrect article - should be 'une' not 'un' for feminine noun 'pomme'.",
        },
        {
            "content": "Je mange des pommes.",
            "is_correct": True,
            "translation": "I eat apples.",
        },
    ]


@pytest.fixture
def sample_problem_data(
    sample_grammar_statements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Sample problem data for testing."""
    return {
        "problem_type": ProblemType.GRAMMAR,
        "title": "Article Agreement",
        "instructions": "Choose the grammatically correct sentence.",
        "correct_answer_index": 0,
        "target_language_code": "eng",
        "statements": sample_grammar_statements,
        "topic_tags": ["grammar", "articles", "agreement"],
        "source_statement_ids": [uuid4(), uuid4()],
        "metadata": {"difficulty": "intermediate", "created_by": "ai"},
    }


@pytest.mark.unit
class TestProblemEnums:
    """Test cases for problem-related enums."""

    def test_problem_type_enum_values(self):
        """Test that problem type enum has correct values."""
        assert ProblemType.GRAMMAR == "grammar"
        # Note: FUNCTIONAL and VOCABULARY types removed as they're not implemented yet

    def test_difficulty_level_enum(self):
        """Test the values of the DifficultyLevel enum."""
        assert DifficultyLevel.BEGINNER == "beginner"
        assert DifficultyLevel.ELEMENTARY == "elementary"
        assert DifficultyLevel.INTERMEDIATE == "intermediate"
        assert DifficultyLevel.UPPER_INTERMEDIATE == "upper_intermediate"
        assert DifficultyLevel.ADVANCED == "advanced"
        assert DifficultyLevel.NATIVE == "native"


@pytest.mark.unit
class TestProblemBase:
    """Test cases for the ProblemBase schema."""

    def test_valid_problem_creation(self, sample_problem_data: dict[str, Any]):
        """Test that a valid ProblemBase model can be created."""
        problem = ProblemBase(**sample_problem_data)
        assert problem.problem_type == ProblemType.GRAMMAR
        assert problem.title == "Article Agreement"
        assert problem.instructions == "Choose the grammatically correct sentence."
        assert problem.correct_answer_index == 0
        assert problem.target_language_code == "eng"
        assert len(problem.statements) == 3
        assert problem.topic_tags == ["grammar", "articles", "agreement"]

    @pytest.mark.parametrize(
        "field_to_remove", ["problem_type", "instructions", "statements"]
    )
    def test_missing_required_fields_fail(
        self, field_to_remove: str, sample_problem_data: dict[str, Any]
    ):
        """Test that missing required fields raise a validation error."""
        invalid_data = sample_problem_data.copy()
        del invalid_data[field_to_remove]
        with pytest.raises(ValidationError):
            ProblemBase(**invalid_data)

    def test_correct_answer_index_validation(self, sample_problem_data: dict[str, Any]):
        """Test correct_answer_index validation."""
        # Test valid index
        valid_data = sample_problem_data.copy()
        valid_data["correct_answer_index"] = 2
        problem = ProblemBase(**valid_data)
        assert problem.correct_answer_index == 2

        # Test invalid index (negative)
        invalid_data = sample_problem_data.copy()
        invalid_data["correct_answer_index"] = -1
        with pytest.raises(ValidationError):
            ProblemBase(**invalid_data)

        # Test index out of bounds
        invalid_data = sample_problem_data.copy()
        invalid_data["correct_answer_index"] = 5  # Only 3 statements
        with pytest.raises(ValidationError):
            ProblemBase(**invalid_data)

    @pytest.mark.parametrize(
        "invalid_code", ["en", "english", "e", "", "1234", "fr-FR"]
    )
    def test_invalid_language_code_validation(
        self, invalid_code: str, sample_problem_data: dict[str, Any]
    ):
        """Test that invalid language codes raise a validation error."""
        invalid_data = sample_problem_data.copy()
        invalid_data["target_language_code"] = invalid_code
        with pytest.raises(ValidationError):
            ProblemBase(**invalid_data)

    @pytest.mark.parametrize("valid_code", ["eng", "fra", "spa", "deu", "ENG"])
    def test_valid_language_code_validation(
        self, valid_code: str, sample_problem_data: dict[str, Any]
    ):
        """Test that valid language codes are accepted."""
        valid_data = sample_problem_data.copy()
        valid_data["target_language_code"] = valid_code
        problem = ProblemBase(**valid_data)
        assert problem.target_language_code == valid_code

    def test_empty_statements_validation(self, sample_problem_data: dict[str, Any]):
        """Test that empty statements array raises validation error."""
        invalid_data = sample_problem_data.copy()
        invalid_data["statements"] = []
        with pytest.raises(ValidationError):
            ProblemBase(**invalid_data)


@pytest.mark.unit
class TestGrammarProblemValidation:
    """Test cases for grammar problem statement validation."""

    def test_valid_grammar_statements(
        self, sample_grammar_statements: list[dict[str, Any]]
    ):
        """Test that valid grammar statements pass validation."""
        problem_data = {
            "problem_type": ProblemType.GRAMMAR,
            "instructions": "Choose the correct sentence.",
            "correct_answer_index": 0,
            "statements": sample_grammar_statements,
        }
        problem = ProblemBase(**problem_data)
        assert len(problem.statements) == 3

    def test_grammar_statement_missing_content(
        self, sample_grammar_statements: list[dict[str, Any]]
    ):
        """Test that grammar statements without content field fail validation."""
        invalid_statements = sample_grammar_statements.copy()
        del invalid_statements[0]["content"]

        problem_data = {
            "problem_type": ProblemType.GRAMMAR,
            "instructions": "Choose the correct sentence.",
            "correct_answer_index": 0,
            "statements": invalid_statements,
        }
        with pytest.raises(ValidationError) as exc_info:
            ProblemBase(**problem_data)
        assert 'must have "content" field' in str(exc_info.value)

    def test_grammar_statement_missing_is_correct(
        self, sample_grammar_statements: list[dict[str, Any]]
    ):
        """Test that grammar statements without is_correct field fail validation."""
        invalid_statements = sample_grammar_statements.copy()
        del invalid_statements[0]["is_correct"]

        problem_data = {
            "problem_type": ProblemType.GRAMMAR,
            "instructions": "Choose the correct sentence.",
            "correct_answer_index": 0,
            "statements": invalid_statements,
        }
        with pytest.raises(ValidationError) as exc_info:
            ProblemBase(**problem_data)
        assert 'must have "is_correct" field' in str(exc_info.value)

    def test_correct_grammar_statement_missing_translation(
        self, sample_grammar_statements: list[dict[str, Any]]
    ):
        """Test that correct grammar statements without translation fail validation."""
        invalid_statements = sample_grammar_statements.copy()
        del invalid_statements[0]["translation"]  # First statement is correct

        problem_data = {
            "problem_type": ProblemType.GRAMMAR,
            "instructions": "Choose the correct sentence.",
            "correct_answer_index": 0,
            "statements": invalid_statements,
        }
        with pytest.raises(ValidationError) as exc_info:
            ProblemBase(**problem_data)
        assert 'must have "translation" field' in str(exc_info.value)

    def test_incorrect_grammar_statement_missing_explanation(
        self, sample_grammar_statements: list[dict[str, Any]]
    ):
        """Test that incorrect grammar statements without explanation fail validation."""
        invalid_statements = sample_grammar_statements.copy()
        del invalid_statements[1]["explanation"]  # Second statement is incorrect

        problem_data = {
            "problem_type": ProblemType.GRAMMAR,
            "instructions": "Choose the correct sentence.",
            "correct_answer_index": 0,
            "statements": invalid_statements,
        }
        with pytest.raises(ValidationError) as exc_info:
            ProblemBase(**problem_data)
        assert 'must have "explanation" field' in str(exc_info.value)


@pytest.mark.unit
class TestProblemCreate:
    """Test cases for the ProblemCreate schema."""

    def test_valid_problem_create(self, sample_problem_data: dict[str, Any]):
        """Test that a valid ProblemCreate model can be created."""
        problem = ProblemCreate(**sample_problem_data)
        assert problem.problem_type == ProblemType.GRAMMAR
        assert problem.title == "Article Agreement"
        assert problem.instructions == "Choose the grammatically correct sentence."

    def test_problem_create_inherits_validation(
        self, sample_problem_data: dict[str, Any]
    ):
        """Test that ProblemCreate inherits validation from ProblemBase."""
        invalid_data = sample_problem_data.copy()
        invalid_data["correct_answer_index"] = 10  # Out of bounds
        with pytest.raises(ValidationError):
            ProblemCreate(**invalid_data)


@pytest.mark.unit
class TestProblemUpdate:
    """Test cases for the ProblemUpdate schema."""

    def test_valid_partial_update(self):
        """Test that a valid partial update can be performed."""
        update_data = {
            "title": "Updated Title",
            "instructions": "Updated instructions",
            "correct_answer_index": 1,
        }
        problem_update = ProblemUpdate(**update_data)
        assert problem_update.title == "Updated Title"
        assert problem_update.instructions == "Updated instructions"
        assert problem_update.correct_answer_index == 1
        assert problem_update.problem_type is None

    def test_update_with_no_fields(self):
        """Test that an update with no fields is valid."""
        problem_update = ProblemUpdate()
        assert problem_update.model_dump(exclude_unset=True) == {}

    def test_update_correct_answer_index_validation(
        self, sample_grammar_statements: list[dict[str, Any]]
    ):
        """Test that correct_answer_index validation works in updates."""
        # Valid update
        update_data = {
            "statements": sample_grammar_statements,
            "correct_answer_index": 2,
        }
        problem_update = ProblemUpdate(**update_data)
        assert problem_update.correct_answer_index == 2

        # Invalid update (out of bounds)
        invalid_update = {
            "statements": sample_grammar_statements,
            "correct_answer_index": 5,
        }
        with pytest.raises(ValidationError):
            ProblemUpdate(**invalid_update)

    @pytest.mark.parametrize(
        "invalid_code", ["en", "english", "e", "", "1234", "fr-FR"]
    )
    def test_invalid_language_code_validation_update(self, invalid_code: str):
        """Test that invalid language codes raise a validation error in updates."""
        with pytest.raises(ValidationError):
            ProblemUpdate(target_language_code=invalid_code)


@pytest.mark.unit
class TestProblem:
    """Test cases for the Problem schema."""

    def test_problem_with_database_fields(self, sample_problem_data: dict[str, Any]):
        """Test that Problem model includes database fields."""
        problem_data = sample_problem_data.copy()
        problem_data.update(
            {
                "id": uuid4(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        )
        problem = Problem(**problem_data)
        assert problem.id is not None
        assert problem.created_at is not None
        assert problem.updated_at is not None
        assert problem.problem_type == ProblemType.GRAMMAR


@pytest.mark.unit
class TestProblemSummary:
    """Test cases for the ProblemSummary schema."""

    def test_problem_summary_fields(self, sample_problem_data: dict[str, Any]):
        """Test that ProblemSummary contains correct fields."""
        summary_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Test Problem",
            "instructions": "Test instructions",
            "correct_answer_index": 0,
            "topic_tags": ["test"],
            "created_at": datetime.now(),
            "statement_count": 3,
        }
        summary = ProblemSummary(**summary_data)
        assert summary.id is not None
        assert summary.problem_type == ProblemType.GRAMMAR
        assert summary.statement_count == 3

    def test_problem_summary_with_focus(self):
        """Test that ProblemSummary accepts focus field."""
        summary_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Conjugation Problem",
            "instructions": "Test instructions",
            "correct_answer_index": 0,
            "topic_tags": ["grammar"],
            "focus": GrammarFocus.CONJUGATION,
            "created_at": datetime.now(),
            "statement_count": 4,
        }
        summary = ProblemSummary(**summary_data)
        assert summary.focus == GrammarFocus.CONJUGATION

    def test_problem_summary_focus_optional(self):
        """Test that ProblemSummary focus is optional and defaults to None."""
        summary_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Test Problem",
            "instructions": "Test instructions",
            "correct_answer_index": 0,
            "topic_tags": ["test"],
            "created_at": datetime.now(),
            "statement_count": 3,
        }
        summary = ProblemSummary(**summary_data)
        assert summary.focus is None

    def test_problem_summary_focus_pronouns(self):
        """Test that ProblemSummary accepts pronouns focus."""
        summary_data = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Pronouns Problem",
            "instructions": "Test instructions",
            "correct_answer_index": 0,
            "topic_tags": ["grammar"],
            "focus": GrammarFocus.PRONOUNS,
            "created_at": datetime.now(),
            "statement_count": 4,
        }
        summary = ProblemSummary(**summary_data)
        assert summary.focus == GrammarFocus.PRONOUNS


@pytest.mark.unit
class TestProblemConstraints:
    """Test cases for problem constraint models."""

    def test_grammar_problem_constraints(self):
        """Test GrammarProblemConstraints model."""
        constraints = GrammarProblemConstraints(
            grammatical_focus=["articles", "agreement"],
            verb_infinitives=["être", "avoir"],
            tenses_used=["present", "past"],
            includes_negation=True,
            includes_cod=False,
            includes_coi=True,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
        )
        assert constraints.grammatical_focus == ["articles", "agreement"]
        assert constraints.verb_infinitives == ["être", "avoir"]
        assert constraints.tenses_used == ["present", "past"]
        assert constraints.includes_negation is True
        assert constraints.includes_cod is False
        assert constraints.includes_coi is True
        assert constraints.difficulty_level == DifficultyLevel.INTERMEDIATE


@pytest.mark.unit
class TestProblemFilters:
    """Test cases for the ProblemFilters schema."""

    def test_problem_filters_defaults(self):
        """Test ProblemFilters with default values."""
        filters = ProblemFilters()
        assert filters.problem_type is None
        assert filters.grammatical_focus is None
        assert filters.tenses_used is None
        assert filters.limit == 50
        assert filters.offset == 0

    def test_problem_filters_with_values(self):
        """Test ProblemFilters with specified values."""
        filters = ProblemFilters(
            problem_type=ProblemType.GRAMMAR,
            topic_tags=["articles", "grammar"],
            target_language_code="fra",
            limit=100,
            offset=25,
        )
        assert filters.problem_type == ProblemType.GRAMMAR
        assert filters.topic_tags == ["articles", "grammar"]
        assert filters.target_language_code == "fra"
        assert filters.limit == 100
        assert filters.offset == 25

    def test_problem_filters_with_grammatical_focus(self):
        """Test ProblemFilters with grammatical_focus filter."""
        filters = ProblemFilters(grammatical_focus=["conjugation"])
        assert filters.grammatical_focus == ["conjugation"]

        filters = ProblemFilters(grammatical_focus=["pronouns"])
        assert filters.grammatical_focus == ["pronouns"]

        filters = ProblemFilters(grammatical_focus=["conjugation", "pronouns"])
        assert filters.grammatical_focus == ["conjugation", "pronouns"]

    def test_problem_filters_with_tenses_used(self):
        """Test ProblemFilters with tenses_used filter."""
        filters = ProblemFilters(tenses_used=["futur_simple"])
        assert filters.tenses_used == ["futur_simple"]

        filters = ProblemFilters(tenses_used=["futur_simple", "imparfait"])
        assert filters.tenses_used == ["futur_simple", "imparfait"]

    def test_problem_filters_grammatical_focus_with_other_filters(self):
        """Test ProblemFilters combining grammatical_focus with other filters."""
        filters = ProblemFilters(
            problem_type=ProblemType.GRAMMAR,
            grammatical_focus=["conjugation"],
            tenses_used=["futur_simple"],
            target_language_code="eng",
            limit=10,
        )
        assert filters.problem_type == ProblemType.GRAMMAR
        assert filters.grammatical_focus == ["conjugation"]
        assert filters.tenses_used == ["futur_simple"]
        assert filters.target_language_code == "eng"
        assert filters.limit == 10

    def test_problem_filters_validation(self):
        """Test ProblemFilters validation."""
        # Test limit validation
        with pytest.raises(ValidationError):
            ProblemFilters(limit=0)  # Below minimum

        with pytest.raises(ValidationError):
            ProblemFilters(limit=2000)  # Above maximum

        # Test offset validation
        with pytest.raises(ValidationError):
            ProblemFilters(offset=-1)  # Below minimum


@pytest.mark.unit
class TestProblemSearchModels:
    """Test cases for problem search request and response models."""

    def test_problem_search_request_defaults(self):
        """Test ProblemSearchRequest with default values."""
        request = ProblemSearchRequest()
        assert request.filters is not None
        assert request.include_statements is True
        assert request.include_metadata is True

    def test_problem_search_request_with_filters(self):
        """Test ProblemSearchRequest with custom filters."""
        filters = ProblemFilters(problem_type=ProblemType.GRAMMAR, limit=25)
        request = ProblemSearchRequest(
            filters=filters,
            include_statements=False,
            include_metadata=False,
        )
        assert request.filters.problem_type == ProblemType.GRAMMAR
        assert request.filters.limit == 25
        assert request.include_statements is False
        assert request.include_metadata is False

    def test_problem_search_response(self):
        """Test ProblemSearchResponse model."""
        filters = ProblemFilters(problem_type=ProblemType.GRAMMAR)
        response = ProblemSearchResponse(
            problems=[],
            total_count=0,
            has_more=False,
            filters_applied=filters,
        )
        assert response.problems == []
        assert response.total_count == 0
        assert response.has_more is False
        assert response.filters_applied.problem_type == ProblemType.GRAMMAR


@pytest.mark.unit
class TestProblemWithMetadata:
    """Test cases for the ProblemWithMetadata schema."""

    def test_problem_with_metadata_fields(self, sample_problem_data: dict[str, Any]):
        """Test that ProblemWithMetadata contains enriched fields."""
        metadata_data = sample_problem_data.copy()
        metadata_data.update(
            {
                "id": uuid4(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "estimated_difficulty": "intermediate",
                "usage_count": 42,
                "success_rate": 0.75,
            }
        )
        problem_with_metadata = ProblemWithMetadata(**metadata_data)
        assert problem_with_metadata.estimated_difficulty == "intermediate"
        assert problem_with_metadata.usage_count == 42
        assert problem_with_metadata.success_rate == 0.75
        assert problem_with_metadata.problem_type == ProblemType.GRAMMAR
