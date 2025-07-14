"""Unit tests for the ProblemRepository class."""

import pytest
from unittest.mock import MagicMock, patch

from src.repositories.problem_repository import ProblemRepository
from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemType,
    ProblemFilters,
    ProblemUpdate,
)


class TestProblemsRepository:
    """Test suite for the ProblemRepository."""

    @pytest.fixture
    def repository(self):
        """Fixture that provides a ProblemRepository instance with a mock client."""
        mock_client = MagicMock()
        return ProblemRepository(mock_client)

    async def test_create_problem_success(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem_create: ProblemCreate,
        sample_problem: Problem,
    ):
        """Test successful creation of a problem."""
        mock_client = (
            supabase_mock_builder()
            .with_insert_response([sample_problem.model_dump(mode="json")])
            .build()
        )
        repository.client = mock_client

        created_problem = await repository.create_problem(sample_problem_create)

        assert created_problem is not None
        assert created_problem.title == sample_problem.title
        assert created_problem.problem_type == sample_problem.problem_type
        repository.client.table.assert_called_with("problems")
        repository.client.table.return_value.insert.assert_called_once()

    async def test_create_problem_failure(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem_create: ProblemCreate,
    ):
        """Test failure when creating a problem."""
        mock_client = supabase_mock_builder().with_insert_response([]).build()
        repository.client = mock_client

        with pytest.raises(Exception, match="Failed to create problem"):
            await repository.create_problem(sample_problem_create)

    async def test_get_problem_found(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test retrieving a problem that exists."""
        mock_client = (
            supabase_mock_builder()
            .with_select_response([sample_problem.model_dump(mode="json")])
            .build()
        )
        repository.client = mock_client

        problem = await repository.get_problem(sample_problem.id)

        assert problem is not None
        assert problem.id == sample_problem.id
        assert problem.title == sample_problem.title
        repository.client.table.return_value.select.return_value.eq.assert_called_once_with(
            "id", str(sample_problem.id)
        )

    async def test_get_problem_not_found(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test retrieving a problem that doesn't exist."""
        mock_client = supabase_mock_builder().with_select_response([]).build()
        repository.client = mock_client

        problem = await repository.get_problem(sample_problem.id)

        assert problem is None

    async def test_get_problems_with_filters(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test getting problems with filters."""
        mock_client = (
            supabase_mock_builder()
            .with_select_response([sample_problem.model_dump(mode="json")], count=1)
            .build()
        )
        repository.client = mock_client

        filters = ProblemFilters(problem_type=ProblemType.GRAMMAR, limit=10, offset=0)
        problems, total_count = await repository.get_problems(filters)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        assert total_count == 1
        repository.client.table.return_value.select.assert_called_once_with(
            "*", count="exact"
        )

    async def test_get_problems_no_filters(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test getting all problems without filters."""
        mock_client = (
            supabase_mock_builder()
            .with_select_response([sample_problem.model_dump(mode="json")], count=1)
            .build()
        )
        repository.client = mock_client

        filters = ProblemFilters()
        problems, total_count = await repository.get_problems(filters)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        assert total_count == 1

    async def test_get_problems_empty_result(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
    ):
        """Test getting problems when no problems exist."""
        mock_client = supabase_mock_builder().with_select_response([], count=0).build()
        repository.client = mock_client

        filters = ProblemFilters()
        problems, total_count = await repository.get_problems(filters)

        assert len(problems) == 0
        assert total_count == 0

    async def test_update_problem_success(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test successful update of a problem."""
        update_data = ProblemUpdate(title="Updated Problem Title")
        updated_problem_data = {
            **sample_problem.model_dump(mode="json"),
            "title": "Updated Problem Title",
        }

        mock_client = (
            supabase_mock_builder().with_update_response([updated_problem_data]).build()
        )
        repository.client = mock_client

        updated_problem = await repository.update_problem(
            sample_problem.id, update_data
        )

        assert updated_problem is not None
        assert updated_problem.title == "Updated Problem Title"

    async def test_update_problem_not_found(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test updating a problem that doesn't exist."""
        update_data = ProblemUpdate(title="Updated Problem Title")

        mock_client = supabase_mock_builder().with_update_response([]).build()
        repository.client = mock_client

        updated_problem = await repository.update_problem(
            sample_problem.id, update_data
        )

        assert updated_problem is None

    async def test_delete_problem_success(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test successful deletion of a problem."""
        mock_client = (
            supabase_mock_builder()
            .with_delete_response([sample_problem.model_dump(mode="json")])
            .build()
        )
        repository.client = mock_client

        result = await repository.delete_problem(sample_problem.id)

        assert result is True
        repository.client.table.return_value.delete.return_value.eq.assert_called_once_with(
            "id", str(sample_problem.id)
        )

    async def test_delete_problem_not_found(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test deleting a problem that doesn't exist."""
        mock_client = supabase_mock_builder().with_delete_response([]).build()
        repository.client = mock_client

        result = await repository.delete_problem(sample_problem.id)

        assert result is False

    async def test_get_problems_by_type(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test getting problems by type."""
        mock_client = (
            supabase_mock_builder()
            .with_select_response([sample_problem.model_dump(mode="json")])
            .build()
        )
        repository.client = mock_client

        problems = await repository.get_problems_by_type(ProblemType.GRAMMAR, limit=10)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id

    async def test_get_problems_by_topic_tags(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test getting problems by topic tags."""
        mock_client = (
            supabase_mock_builder()
            .with_select_response([sample_problem.model_dump(mode="json")])
            .build()
        )
        repository.client = mock_client

        problems = await repository.get_problems_by_topic_tags(
            ["grammar", "articles"], limit=10
        )

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        repository.client.table.return_value.select.return_value.or_.assert_called_once_with(
            "topic_tags.ov.{grammar,articles}"
        )

    async def test_get_problems_by_topic_tags_empty(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
    ):
        """Test getting problems by topic tags when no problems match."""
        mock_client = supabase_mock_builder().with_select_response([]).build()
        repository.client = mock_client

        problems = await repository.get_problems_by_topic_tags(["nonexistent"])

        assert len(problems) == 0

    @patch("random.choice")
    async def test_get_random_problem(
        self,
        mock_random_choice,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test getting a random problem."""
        mock_client = (
            supabase_mock_builder()
            .with_select_response([sample_problem.model_dump(mode="json")])
            .build()
        )
        repository.client = mock_client
        mock_random_choice.return_value = sample_problem.model_dump(mode="json")

        problem = await repository.get_random_problem(
            problem_type=ProblemType.GRAMMAR, topic_tags=["grammar"]
        )

        assert problem is not None
        assert problem.id == sample_problem.id
        mock_random_choice.assert_called_once()

    @patch("random.choice")
    async def test_get_random_problem_no_problems(
        self,
        mock_random_choice,
        repository: ProblemRepository,
        supabase_mock_builder,
    ):
        """Test getting a random problem when no problems exist."""
        mock_client = supabase_mock_builder().with_select_response([]).build()
        repository.client = mock_client

        problem = await repository.get_random_problem()

        assert problem is None

    async def test_count_problems(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
    ):
        """Test counting problems."""
        mock_client = supabase_mock_builder().with_select_response([], count=42).build()
        repository.client = mock_client

        count = await repository.count_problems()

        assert count == 42

    async def test_get_recent_problems(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
        sample_problem: Problem,
    ):
        """Test getting recent problems."""
        mock_client = (
            supabase_mock_builder()
            .with_select_response([sample_problem.model_dump(mode="json")])
            .build()
        )
        repository.client = mock_client

        problems = await repository.get_recent_problems(limit=5)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id

    async def test_get_recent_problems_empty(
        self,
        repository: ProblemRepository,
        supabase_mock_builder,
    ):
        """Test getting recent problems when none exist."""
        mock_client = supabase_mock_builder().with_select_response([]).build()
        repository.client = mock_client

        problems = await repository.get_recent_problems()

        assert len(problems) == 0
