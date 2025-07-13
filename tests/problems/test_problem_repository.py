"""Unit tests for the ProblemsRepository."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, Any, List

from src.repositories.problem_repository import ProblemRepository
from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemUpdate,
    ProblemType,
    ProblemFilters,
    ProblemSummary,
)


@pytest.fixture
def mock_supabase_client():
    """Provides a mock Supabase client for testing."""
    mock_client = MagicMock()

    # Mock the chain of calls for select
    select_mock = MagicMock()
    select_mock.eq.return_value = select_mock
    select_mock.limit.return_value = select_mock
    select_mock.range.return_value = select_mock
    select_mock.order.return_value = select_mock
    select_mock.gte.return_value = select_mock
    select_mock.lte.return_value = select_mock
    select_mock.contains.return_value = select_mock
    select_mock.or_.return_value = select_mock
    select_mock.execute = AsyncMock()

    # Mock the chain of calls for update
    update_mock = MagicMock()
    update_mock.eq.return_value = update_mock
    update_mock.execute = AsyncMock()

    # Mock the chain of calls for insert
    insert_mock = MagicMock()
    insert_mock.execute = AsyncMock()

    # Mock the chain of calls for delete
    delete_mock = MagicMock()
    delete_mock.eq.return_value = delete_mock
    delete_mock.execute = AsyncMock()

    # Mock the table method to return a mock that has the chained methods
    table_mock = MagicMock()
    table_mock.select.return_value = select_mock
    table_mock.update.return_value = update_mock
    table_mock.insert.return_value = insert_mock
    table_mock.delete.return_value = delete_mock

    mock_client.table.return_value = table_mock
    return mock_client


@pytest.fixture
def repository(mock_supabase_client):
    """Fixture to create a ProblemsRepository with a mock client."""
    return ProblemRepository(client=mock_supabase_client)


@pytest.fixture
def sample_problem_data():
    """Sample problem data for testing."""
    return {
        "id": uuid4(),
        "problem_type": ProblemType.GRAMMAR,
        "title": "Article Agreement",
        "instructions": "Choose the correct sentence",
        "correct_answer_index": 0,
        "target_language_code": "eng",
        "statements": [
            {
                "content": "Je mange une pomme.",
                "is_correct": True,
                "translation": "I eat an apple.",
            },
            {
                "content": "Je mange un pomme.",
                "is_correct": False,
                "explanation": "Wrong article",
            },
        ],
        "topic_tags": ["grammar", "articles"],
        "source_statement_ids": [uuid4(), uuid4()],
        "metadata": {"difficulty": "intermediate"},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_problem_create_data():
    """Sample problem create data for testing."""
    return {
        "problem_type": ProblemType.GRAMMAR,
        "title": "Article Agreement",
        "instructions": "Choose the correct sentence",
        "correct_answer_index": 0,
        "target_language_code": "eng",
        "statements": [
            {
                "content": "Je mange une pomme.",
                "is_correct": True,
                "translation": "I eat an apple.",
            },
            {
                "content": "Je mange un pomme.",
                "is_correct": False,
                "explanation": "Wrong article",
            },
        ],
        "topic_tags": ["grammar", "articles"],
        "source_statement_ids": [uuid4(), uuid4()],
        "metadata": {"difficulty": "intermediate"},
    }


@pytest.fixture
def sample_problem(sample_problem_data):
    """Sample Problem instance for testing."""
    return Problem(**sample_problem_data)


@pytest.fixture
def sample_problem_create(sample_problem_create_data):
    """Sample ProblemCreate instance for testing."""
    return ProblemCreate(**sample_problem_create_data)


@pytest.mark.unit
@pytest.mark.asyncio
class TestProblemsRepository:
    """Test cases for the ProblemsRepository."""

    async def test_create_problem_success(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem_create: ProblemCreate,
        sample_problem: Problem,
    ):
        """Test successful creation of a problem."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        created_problem = await repository.create_problem(sample_problem_create)

        assert created_problem is not None
        assert created_problem.title == sample_problem.title
        assert created_problem.problem_type == sample_problem.problem_type
        repository.client.table.assert_called_with("problems")
        repository.client.table.return_value.insert.assert_called_once()

    async def test_create_problem_failure(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem_create: ProblemCreate,
    ):
        """Test problem creation failure."""
        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        with pytest.raises(Exception, match="Failed to create problem"):
            await repository.create_problem(sample_problem_create)

    async def test_get_problem_found(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test retrieving a problem that exists."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

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
        mock_supabase_client: MagicMock,
    ):
        """Test retrieving a problem that doesn't exist."""
        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        problem = await repository.get_problem(uuid4())

        assert problem is None

    async def test_get_problems_with_filters(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting problems with filters."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_response.count = 1
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.range.return_value.execute.return_value = mock_response

        filters = ProblemFilters(problem_type=ProblemType.GRAMMAR, limit=10, offset=0)
        problems, total_count = await repository.get_problems(filters)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        assert total_count == 1
        repository.client.table.return_value.select.assert_called_once_with(
            "*", count="exact"
        )

    async def test_get_problems_without_statements(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting problems without statements."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_response.count = 1
        mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.return_value = mock_response

        filters = ProblemFilters(limit=10, offset=0)
        problems, total_count = await repository.get_problems(
            filters, include_statements=False
        )

        assert len(problems) == 1
        # Should call select with limited fields
        expected_fields = """
            id, created_at, updated_at, problem_type, title, instructions, 
            correct_answer_index, target_language_code, topic_tags, 
            source_statement_ids, metadata
        """
        repository.client.table.return_value.select.assert_called_once_with(
            expected_fields, count="exact"
        )

    async def test_get_problem_summaries(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting problem summaries."""
        mock_response = MagicMock()
        summary_data = {
            "id": sample_problem.id,
            "problem_type": sample_problem.problem_type,
            "title": sample_problem.title,
            "instructions": sample_problem.instructions,
            "correct_answer_index": sample_problem.correct_answer_index,
            "topic_tags": sample_problem.topic_tags,
            "created_at": sample_problem.created_at,
            "statement_count": 2,
        }
        mock_response.data = [summary_data]
        mock_response.count = 1
        mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.return_value = mock_response

        filters = ProblemFilters(limit=10, offset=0)
        summaries, total_count = await repository.get_problem_summaries(filters)

        assert len(summaries) == 1
        assert isinstance(summaries[0], ProblemSummary)
        assert summaries[0].id == sample_problem.id
        assert summaries[0].statement_count == 2
        assert total_count == 1

    async def test_update_problem_success(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test successful problem update."""
        mock_response = MagicMock()
        updated_data = sample_problem.model_dump(mode="json")
        updated_data["title"] = "Updated Title"
        mock_response.data = [updated_data]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        update_data = ProblemUpdate(title="Updated Title")
        updated_problem = await repository.update_problem(
            sample_problem.id, update_data
        )

        assert updated_problem is not None
        assert updated_problem.title == "Updated Title"
        repository.client.table.return_value.update.return_value.eq.assert_called_once_with(
            "id", str(sample_problem.id)
        )

    async def test_update_problem_not_found(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test updating a problem that doesn't exist."""
        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        update_data = ProblemUpdate(title="Updated Title")
        updated_problem = await repository.update_problem(uuid4(), update_data)

        assert updated_problem is None

    async def test_delete_problem_success(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test successful problem deletion."""
        mock_response = MagicMock()
        mock_response.data = [{"id": str(sample_problem.id)}]
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

        result = await repository.delete_problem(sample_problem.id)

        assert result is True
        repository.client.table.return_value.delete.return_value.eq.assert_called_once_with(
            "id", str(sample_problem.id)
        )

    async def test_delete_problem_not_found(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test deleting a problem that doesn't exist."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

        result = await repository.delete_problem(uuid4())

        assert result is False

    async def test_get_problems_by_type(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting problems by type."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response

        problems = await repository.get_problems_by_type(ProblemType.GRAMMAR, limit=10)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        repository.client.table.return_value.select.return_value.eq.assert_called_once_with(
            "problem_type", ProblemType.GRAMMAR.value
        )

    async def test_get_problems_by_topic_tags(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting problems by topic tags."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response

        problems = await repository.get_problems_by_topic_tags(
            ["grammar", "articles"], limit=10
        )

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        repository.client.table.return_value.select.return_value.or_.assert_called_once_with(
            "topic_tags.ov.{grammar,articles}"
        )

    async def test_get_problems_using_statement(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting problems using a specific statement."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.contains.return_value.limit.return_value.execute.return_value = mock_response

        statement_id = uuid4()
        problems = await repository.get_problems_using_statement(statement_id, limit=10)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        repository.client.table.return_value.select.return_value.contains.assert_called_once_with(
            "source_statement_ids", [str(statement_id)]
        )

    async def test_search_problems_by_metadata(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test searching problems by metadata."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.contains.return_value.limit.return_value.execute.return_value = mock_response

        metadata_query = {"difficulty": "intermediate"}
        problems = await repository.search_problems_by_metadata(
            metadata_query, limit=10
        )

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        repository.client.table.return_value.select.return_value.contains.assert_called_once_with(
            "metadata", metadata_query
        )

    @patch("random.choice")
    async def test_get_random_problem(
        self,
        mock_random_choice,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting a random problem."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.or_.return_value.limit.return_value.execute.return_value = mock_response
        mock_random_choice.return_value = sample_problem.model_dump(mode="json")

        problem = await repository.get_random_problem(
            problem_type=ProblemType.GRAMMAR, topic_tags=["grammar"]
        )

        assert problem is not None
        assert problem.id == sample_problem.id
        mock_random_choice.assert_called_once()

    async def test_get_random_problem_no_results(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test getting a random problem when no results exist."""
        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response

        problem = await repository.get_random_problem()

        assert problem is None

    async def test_count_problems(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test counting problems."""
        mock_response = MagicMock()
        mock_response.count = 42
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response

        count = await repository.count_problems()

        assert count == 42
        repository.client.table.return_value.select.assert_called_once_with(
            "id", count="exact"
        )

    async def test_count_problems_with_filters(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test counting problems with filters."""
        mock_response = MagicMock()
        mock_response.count = 10
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.or_.return_value.execute.return_value = mock_response

        count = await repository.count_problems(
            problem_type=ProblemType.GRAMMAR, topic_tags=["grammar"]
        )

        assert count == 10

    async def test_get_problem_statistics(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test getting problem statistics."""
        # Mock response for total count (first call)
        total_mock_response = MagicMock()
        total_mock_response.count = 100

        # Mock response for type-specific counts
        type_mock_response = MagicMock()
        type_mock_response.count = 30

        # Create separate mock chains for different calls
        total_select_mock = MagicMock()
        total_select_mock.execute = AsyncMock(return_value=total_mock_response)

        type_select_mock = MagicMock()
        type_select_mock.execute = AsyncMock(return_value=type_mock_response)

        # Set up the mock to return different chains for different calls
        def mock_select(*args, **kwargs):
            # First call is for total count
            if not hasattr(mock_select, "call_count"):
                mock_select.call_count = 0
            mock_select.call_count += 1

            if mock_select.call_count == 1:
                return total_select_mock
            else:
                type_chain = MagicMock()
                type_chain.eq.return_value = type_select_mock
                return type_chain

        mock_supabase_client.table.return_value.select.side_effect = mock_select

        stats = await repository.get_problem_statistics()

        assert stats["total_problems"] == 100
        assert "problems_by_type" in stats
        assert len(stats["problems_by_type"]) == len(ProblemType)
        for problem_type in ProblemType:
            assert stats["problems_by_type"][problem_type.value] == 30

    async def test_get_problems_with_topic_tag(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting problems with a specific topic tag."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.contains.return_value.limit.return_value.execute.return_value = mock_response

        problems = await repository.get_problems_with_topic_tag("grammar", limit=10)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        repository.client.table.return_value.select.return_value.contains.assert_called_once_with(
            "topic_tags", ["grammar"]
        )

    async def test_get_recent_problems(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        sample_problem: Problem,
    ):
        """Test getting recent problems."""
        mock_response = MagicMock()
        mock_response.data = [sample_problem.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = mock_response

        problems = await repository.get_recent_problems(limit=5)

        assert len(problems) == 1
        assert problems[0].id == sample_problem.id
        repository.client.table.return_value.select.return_value.order.assert_called_once_with(
            "created_at", desc=True
        )

    @pytest.mark.parametrize(
        "filter_data,expected_calls",
        [
            (
                {"problem_type": ProblemType.GRAMMAR},
                [("eq", "problem_type", ProblemType.GRAMMAR.value)],
            ),
            (
                {"target_language_code": "fra"},
                [("eq", "target_language_code", "fra")],
            ),
            (
                {"topic_tags": ["grammar", "articles"]},
                [("or_", "topic_tags.ov.{grammar,articles}")],
            ),
            (
                {"created_after": datetime(2023, 1, 1, tzinfo=timezone.utc)},
                [("gte", "created_at", "2023-01-01T00:00:00+00:00")],
            ),
            (
                {"created_before": datetime(2023, 12, 31, tzinfo=timezone.utc)},
                [("lte", "created_at", "2023-12-31T00:00:00+00:00")],
            ),
            (
                {"metadata_contains": {"difficulty": "intermediate"}},
                [("contains", "metadata", {"difficulty": "intermediate"})],
            ),
        ],
    )
    async def test_apply_filters_parameterized(
        self,
        repository: ProblemRepository,
        mock_supabase_client: MagicMock,
        filter_data: Dict[str, Any],
        expected_calls: List[tuple],
    ):
        """Test that filters are applied correctly."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.count = 0

        # Set up the mock chain
        mock_query = mock_supabase_client.table.return_value.select.return_value
        for method, *args in expected_calls:
            mock_query = getattr(mock_query, method).return_value
        mock_query.range.return_value.execute.return_value = mock_response

        filters = ProblemFilters(**filter_data)
        await repository.get_problems(filters)

        # Verify the filter methods were called
        query_mock = mock_supabase_client.table.return_value.select.return_value
        for method, *args in expected_calls:
            getattr(query_mock, method).assert_called_once_with(*args)
            query_mock = getattr(query_mock, method).return_value


@pytest.mark.unit
@pytest.mark.asyncio
class TestProblemsRepositoryClassMethods:
    """Test cases for ProblemsRepository class methods."""

    @patch("src.repositories.problem_repository.get_supabase_client")
    async def test_create_with_default_client(self, mock_get_client):
        """Test creating repository with default client."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        repository = await ProblemRepository.create()

        assert repository.client == mock_client
        mock_get_client.assert_called_once()

    async def test_create_with_provided_client(self):
        """Test creating repository with provided client."""
        mock_client = MagicMock()

        repository = await ProblemRepository.create(client=mock_client)

        assert repository.client == mock_client
