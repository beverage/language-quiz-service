"""Tests for CLI problems functionality."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from src.cli.problems.create import (
    generate_random_problem,
    generate_random_problems_batch,
    get_problem_statistics,
    get_random_grammar_problem,
    list_problems,
)
from src.schemas.problems import (
    GrammarFocus,
    GrammarProblemConstraints,
    Problem,
    ProblemSummary,
    ProblemType,
)

# Filter expected warnings from async mocking
pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


@pytest.fixture
def sample_problem():
    """Fixture for a sample Problem."""
    return Problem(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        problem_type=ProblemType.GRAMMAR,
        title="Test Grammar Problem",
        instructions="Choose the correct verb form",
        correct_answer_index=0,
        target_language_code="eng",
        statements=[
            {
                "content": "J'ai un livre.",
                "is_correct": True,
                "translation": "I have a book.",
            },
            {
                "content": "Je ai un livre.",
                "is_correct": False,
                "explanation": "Incorrect contraction - should be 'j'ai'",
            },
            {
                "content": "J'aie un livre.",
                "is_correct": False,
                "explanation": "Wrong subjunctive mood - should be indicative 'ai'",
            },
            {
                "content": "J'avoir un livre.",
                "is_correct": False,
                "explanation": "Using infinitive instead of conjugated form",
            },
        ],
        topic_tags=["basic_conjugation", "avoir_verb"],
        source_statement_ids=[],
        metadata={
            "grammatical_focus": ["verb_conjugation", "auxiliary_verbs"],
            "verb_infinitive": "avoir",
            "difficulty_estimated": "beginner",
        },
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_problem_summary():
    """Fixture for a sample ProblemSummary."""
    return ProblemSummary(
        id=UUID("87654321-4321-8765-4321-876543218765"),
        problem_type=ProblemType.GRAMMAR,
        title="Grammar Summary Test",
        instructions="Test instructions",
        correct_answer_index=1,
        topic_tags=["grammar", "test"],
        created_at=datetime(2023, 1, 2, 10, 0, 0),
        statement_count=4,
    )


@pytest.fixture
def sample_constraints():
    """Fixture for sample GrammarProblemConstraints."""
    return GrammarProblemConstraints(
        grammatical_focus=["verb_conjugation"],
        verb_infinitives=["avoir", "être"],
        tenses_used=["present", "passe_compose"],
        includes_negation=False,
        includes_cod=True,
        includes_coi=False,
    )


@pytest.fixture
def mock_problem_service():
    """Fixture for mocked ProblemService."""
    return AsyncMock()


@pytest.mark.unit
class TestCLIProblemsCreation:
    """Test cases for CLI problem creation functions."""

    @patch("src.cli.problems.create.create_problem_service")
    async def test_generate_random_problem_success_no_display(
        self,
        mock_create_problem_service: MagicMock,
        sample_problem: Problem,
        sample_constraints: GrammarProblemConstraints,
    ):
        """Test successful problem generation without display."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.create_random_grammar_problem.return_value = sample_problem

        result = await generate_random_problem(
            statement_count=4, constraints=sample_constraints, display=False
        )

        assert result == sample_problem
        mock_service.create_random_grammar_problem.assert_called_once_with(
            constraints=sample_constraints, statement_count=4, focus=None
        )

    @patch("src.cli.problems.create.create_problem_service")
    async def test_generate_random_problem_success_with_display(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test successful problem generation with display."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.create_random_grammar_problem.return_value = sample_problem

        with patch("builtins.print"):  # Mock print to avoid display output
            result = await generate_random_problem(
                statement_count=3, constraints=None, display=True
            )

        assert result == sample_problem
        mock_service.create_random_grammar_problem.assert_called_once_with(
            constraints=None, statement_count=3, focus=None
        )

    @patch("src.cli.problems.create.create_problem_service")
    async def test_generate_random_problem_service_failure(
        self, mock_create_problem_service: MagicMock
    ):
        """Test problem generation when service raises exception."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.create_random_grammar_problem.side_effect = ValueError(
            "Service error"
        )

        with pytest.raises(ValueError, match="Service error"):
            await generate_random_problem(statement_count=4)

    @patch("src.cli.problems.create.create_problem_service")
    async def test_generate_random_problem_with_conjugation_focus(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test problem generation with explicit conjugation focus."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.create_random_grammar_problem.return_value = sample_problem

        result = await generate_random_problem(
            statement_count=4, focus=GrammarFocus.CONJUGATION, display=False
        )

        assert result == sample_problem
        mock_service.create_random_grammar_problem.assert_called_once_with(
            constraints=None,
            statement_count=4,
            focus=GrammarFocus.CONJUGATION,
        )

    @patch("src.cli.problems.create.create_problem_service")
    async def test_generate_random_problem_with_pronouns_focus(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test problem generation with explicit pronouns focus."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.create_random_grammar_problem.return_value = sample_problem

        result = await generate_random_problem(
            statement_count=4, focus=GrammarFocus.PRONOUNS, display=False
        )

        assert result == sample_problem
        mock_service.create_random_grammar_problem.assert_called_once_with(
            constraints=None,
            statement_count=4,
            focus=GrammarFocus.PRONOUNS,
        )

    @patch("src.cli.problems.create.create_problem_service")
    async def test_generate_random_problem_none_focus_passes_to_service(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test that None focus is passed to service for random selection."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.create_random_grammar_problem.return_value = sample_problem

        result = await generate_random_problem(
            statement_count=4, focus=None, display=False
        )

        assert result == sample_problem
        # Verify focus=None is explicitly passed (service does random selection)
        mock_service.create_random_grammar_problem.assert_called_once_with(
            constraints=None,
            statement_count=4,
            focus=None,
        )

    @patch("src.cli.utils.queues.parallel_execute")
    async def test_generate_random_problems_batch_success(
        self,
        mock_parallel_execute: AsyncMock,
        sample_problem: Problem,
        sample_constraints: GrammarProblemConstraints,
    ):
        """Test successful batch problem generation."""
        problems = [sample_problem, sample_problem, sample_problem]
        mock_parallel_execute.return_value = problems

        result = await generate_random_problems_batch(
            quantity=3,
            statement_count=4,
            constraints=sample_constraints,
            workers=5,
            display=False,
        )

        assert result == problems
        assert len(result) == 3
        mock_parallel_execute.assert_called_once()

        # Verify the call arguments
        call_args = mock_parallel_execute.call_args
        assert call_args.kwargs["max_concurrent"] == 5
        assert call_args.kwargs["batch_delay"] == 0.5
        assert len(call_args.kwargs["tasks"]) == 3

    @patch("src.cli.utils.queues.parallel_execute")
    async def test_generate_random_problems_batch_with_display(
        self, mock_parallel_execute: AsyncMock, sample_problem: Problem
    ):
        """Test batch problem generation with display output."""
        problems = [sample_problem, sample_problem]
        mock_parallel_execute.return_value = problems

        with patch("builtins.print"):  # Mock print to avoid display output
            result = await generate_random_problems_batch(quantity=2, display=True)

        assert result == problems

    @patch("src.cli.utils.queues.parallel_execute")
    async def test_generate_random_problems_batch_empty_results(
        self, mock_parallel_execute: AsyncMock
    ):
        """Test batch generation when no problems are successfully created."""
        mock_parallel_execute.return_value = []

        result = await generate_random_problems_batch(quantity=3, display=True)

        assert result == []


@pytest.mark.unit
class TestCLIProblemsListing:
    """Test cases for CLI problem listing and search functions."""

    @patch("src.cli.problems.create.create_problem_service")
    async def test_list_problems_verbose_mode(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test listing problems in verbose mode."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.get_problems.return_value = ([sample_problem], 1)

        with patch("builtins.print"):
            problems, total = await list_problems(
                problem_type="grammar", topic_tags=["test"], limit=5, verbose=True
            )

        assert problems == [sample_problem]
        assert total == 1

        # Verify service was called with correct filters
        call_args = mock_service.get_problems.call_args
        filters = call_args[0][0]
        assert filters.problem_type == ProblemType.GRAMMAR
        assert filters.topic_tags == ["test"]
        assert filters.limit == 5

    @patch("src.cli.problems.create.create_problem_service")
    async def test_list_problems_summary_mode(
        self,
        mock_create_problem_service: MagicMock,
        sample_problem_summary: ProblemSummary,
    ):
        """Test listing problems in summary mode."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.get_problem_summaries.return_value = ([sample_problem_summary], 1)

        with patch("builtins.print"):
            summaries, total = await list_problems(
                problem_type=None, topic_tags=None, limit=10, verbose=False
            )

        assert summaries == [sample_problem_summary]
        assert total == 1
        mock_service.get_problem_summaries.assert_called_once()

    @pytest.mark.parametrize(
        "problem_type,expected_type",
        [
            ("grammar", ProblemType.GRAMMAR),
            ("functional", ProblemType.FUNCTIONAL),
            ("vocabulary", ProblemType.VOCABULARY),
            (None, None),
        ],
    )
    @patch("src.cli.problems.create.create_problem_service")
    async def test_list_problems_type_filtering(
        self,
        mock_create_problem_service: MagicMock,
        problem_type: str,
        expected_type: ProblemType,
        sample_problem_summary: ProblemSummary,
    ):
        """Test problem type filtering in list function."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.get_problem_summaries.return_value = ([sample_problem_summary], 1)

        with patch("builtins.print"):
            await list_problems(problem_type=problem_type, verbose=False)

        call_args = mock_service.get_problem_summaries.call_args
        filters = call_args[0][0]
        assert filters.problem_type == expected_type

    @patch("src.cli.problems.create.create_problem_service")
    async def test_get_problem_statistics(self, mock_create_problem_service: MagicMock):
        """Test getting problem statistics."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service

        expected_stats = {
            "total_problems": 42,
            "problems_by_type": {"grammar": 30, "functional": 8, "vocabulary": 4},
        }
        mock_service.get_problem_statistics.return_value = expected_stats

        with patch("builtins.print") as mock_print:
            result = await get_problem_statistics()

        assert result == expected_stats
        mock_service.get_problem_statistics.assert_called_once()

        # Verify proper output formatting
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("📊 Problem Statistics:" in call for call in print_calls)
        assert any("Total problems: 42" in call for call in print_calls)


@pytest.mark.unit
class TestCLIProblemsRandomWithFocus:
    """Test cases for get_random_grammar_problem with filters."""

    @patch("src.cli.problems.create.create_problem_service")
    async def test_get_random_grammar_problem_with_conjugation_focus(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test fetching random grammar problem with conjugation focus filter."""
        mock_service = AsyncMock()
        # create_problem_service is async, so make the mock return the service when awaited
        mock_create_problem_service.return_value = mock_service
        mock_service.get_random_grammar_problem.return_value = sample_problem

        from src.cli.problems.create import get_random_grammar_problem

        result = await get_random_grammar_problem(
            grammatical_focus=["conjugation"], display=False
        )

        assert result == sample_problem
        # Verify the service method was called with correct parameters
        mock_service.get_random_grammar_problem.assert_called_once()
        call_kwargs = mock_service.get_random_grammar_problem.call_args.kwargs
        assert call_kwargs["grammatical_focus"] == ["conjugation"]
        assert call_kwargs["tenses_used"] is None
        assert call_kwargs["topic_tags"] is None
        assert call_kwargs["target_language_code"] is None

    @patch("src.cli.problems.create.create_problem_service")
    async def test_get_random_grammar_problem_with_pronouns_focus(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test fetching random grammar problem with pronouns focus filter."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.get_random_grammar_problem.return_value = sample_problem

        from src.cli.problems.create import get_random_grammar_problem

        result = await get_random_grammar_problem(
            grammatical_focus=["pronouns"], display=False
        )

        assert result == sample_problem
        mock_service.get_random_grammar_problem.assert_called_once()
        call_kwargs = mock_service.get_random_grammar_problem.call_args.kwargs
        assert call_kwargs["grammatical_focus"] == ["pronouns"]
        assert call_kwargs["tenses_used"] is None
        assert call_kwargs["topic_tags"] is None
        assert call_kwargs["target_language_code"] is None

    @patch("src.cli.problems.create.create_problem_service")
    async def test_get_random_grammar_problem_with_tenses(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test fetching random grammar problem with tenses filter."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.get_random_grammar_problem.return_value = sample_problem

        from src.cli.problems.create import get_random_grammar_problem

        result = await get_random_grammar_problem(
            tenses_used=["future_simple", "imparfait"], display=False
        )

        assert result == sample_problem
        mock_service.get_random_grammar_problem.assert_called_once()
        call_kwargs = mock_service.get_random_grammar_problem.call_args.kwargs
        assert call_kwargs["grammatical_focus"] is None
        assert call_kwargs["tenses_used"] == ["future_simple", "imparfait"]
        assert call_kwargs["topic_tags"] is None
        assert call_kwargs["target_language_code"] is None

    @patch("src.cli.problems.create.create_problem_service")
    async def test_get_random_grammar_problem_without_filters(
        self, mock_create_problem_service: MagicMock, sample_problem: Problem
    ):
        """Test fetching random grammar problem without filters."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.get_random_grammar_problem.return_value = sample_problem

        from src.cli.problems.create import get_random_grammar_problem

        result = await get_random_grammar_problem(display=False)

        assert result == sample_problem
        mock_service.get_random_grammar_problem.assert_called_once()
        call_kwargs = mock_service.get_random_grammar_problem.call_args.kwargs
        assert call_kwargs["grammatical_focus"] is None
        assert call_kwargs["tenses_used"] is None
        assert call_kwargs["topic_tags"] is None
        assert call_kwargs["target_language_code"] is None


@pytest.mark.unit
class TestCLIProblemsEdgeCases:
    """Test cases for edge cases and error handling."""

    @pytest.mark.parametrize("statement_count,workers", [(1, 1), (10, 5), (100, 20)])
    @patch("src.cli.utils.queues.parallel_execute")
    async def test_generate_problems_batch_various_sizes(
        self,
        mock_parallel_execute: AsyncMock,
        statement_count: int,
        workers: int,
        sample_problem: Problem,
    ):
        """Test batch generation with various sizes and worker counts."""
        mock_parallel_execute.return_value = [sample_problem] * statement_count

        result = await generate_random_problems_batch(
            quantity=statement_count, workers=workers, display=False
        )

        assert len(result) == statement_count
        mock_parallel_execute.assert_called_once()

    @patch("src.cli.problems.create.create_problem_service")
    async def test_list_problems_empty_results(
        self, mock_create_problem_service: MagicMock
    ):
        """Test listing when no problems are found."""
        mock_service = AsyncMock()
        mock_create_problem_service.return_value = mock_service
        mock_service.get_problem_summaries.return_value = ([], 0)

        with patch("builtins.print"):
            problems, total = await list_problems(verbose=False)

        assert problems == []
        assert total == 0
