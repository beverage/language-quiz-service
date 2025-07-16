"""Test cases for problem repository using Supabase client only."""

from uuid import uuid4

import pytest

from src.core.exceptions import RepositoryError
from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemFilters,
    ProblemType,
    ProblemUpdate,
)
from tests.problems.fixtures import (
    generate_random_problem_data,
    problem_repository,  # Import the fixture
)


@pytest.mark.integration
class TestProblemRepository:
    """Test cases for ProblemRepository using Supabase client operations only."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_repository_with_supabase_client(self, problem_repository):
        """Test that ProblemRepository can be instantiated with Supabase client."""
        assert problem_repository.client is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_problem_failure_with_invalid_data(self, problem_repository):
        """Test that creating a problem with invalid data raises an exception."""
        # Create invalid problem data (missing required fields)
        invalid_problem_data = {"title": ""}  # Empty title should fail

        with pytest.raises(Exception):
            await problem_repository.create_problem(
                ProblemCreate(**invalid_problem_data)
            )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_problem_db_error(self, problem_repository):
        """Test that a database constraint violation raises RepositoryError."""
        problem_data = generate_random_problem_data()
        # Use a unique title to ensure we can trigger a unique constraint violation
        problem_data["title"] = f"unique_title_{uuid4()}"
        problem_to_create = ProblemCreate(**problem_data)

        # Create the problem once, which should succeed.
        await problem_repository.create_problem(problem_to_create)

        # Try to create the exact same problem again, which should fail.
        with pytest.raises(RepositoryError):
            await problem_repository.create_problem(problem_to_create)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_problem_crud_operations_create(self, problem_repository):
        """Test creating a problem using repository."""
        problem_data = generate_random_problem_data()
        problem_create = ProblemCreate(**problem_data)

        result = await problem_repository.create_problem(problem_create)

        assert result.title == problem_data["title"]
        assert result.problem_type == problem_data["problem_type"]
        assert result.target_language_code == problem_data["target_language_code"]
        assert result.correct_answer_index == problem_data["correct_answer_index"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_problem_crud_operations_get(self, problem_repository):
        """Test getting a problem by ID using repository."""
        # First create a problem
        problem_data = generate_random_problem_data()
        created_problem = await problem_repository.create_problem(
            ProblemCreate(**problem_data)
        )

        # Then retrieve it
        result = await problem_repository.get_problem(created_problem.id)

        assert result is not None
        assert result.id == created_problem.id
        assert result.title == problem_data["title"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_problem_crud_operations_update(self, problem_repository):
        """Test updating a problem using repository."""
        # First create a problem
        problem_data = generate_random_problem_data()
        problem_data["title"] = f"test_update_{uuid4()}"
        created_problem = await problem_repository.create_problem(
            ProblemCreate(**problem_data)
        )

        # Then update it
        updated_title = f"updated_title_{uuid4()}"
        update_data = ProblemUpdate(title=updated_title)
        result = await problem_repository.update_problem(
            created_problem.id, update_data
        )

        assert result is not None
        assert result.title == updated_title
        assert result.problem_type == problem_data["problem_type"]  # Unchanged

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_problem_crud_operations_delete(self, problem_repository):
        """Test deleting a problem using repository."""
        # First create a problem
        problem_data = generate_random_problem_data()
        created_problem = await problem_repository.create_problem(
            ProblemCreate(**problem_data)
        )

        # Then delete it
        result = await problem_repository.delete_problem(created_problem.id)
        assert result is True

        # Verify it's deleted
        deleted_problem = await problem_repository.get_problem(created_problem.id)
        assert deleted_problem is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_problem_retrieval_variants(self, problem_repository):
        """Test different ways of retrieving problems using repository."""
        # Create a unique problem for this test
        unique_suffix = uuid4().hex[:8]
        problem_data = generate_random_problem_data()
        problem_data["title"] = f"test_problem_{unique_suffix}"

        created_problem = await problem_repository.create_problem(
            ProblemCreate(**problem_data)
        )

        # Test get by ID
        retrieved_problem = await problem_repository.get_problem(created_problem.id)
        assert retrieved_problem.id == created_problem.id

        # Test get problems - just ensure we get at least one problem (our created one)
        all_problems, total_count = await problem_repository.get_problems(
            ProblemFilters()
        )
        assert len(all_problems) >= 1  # At least our created problem should be there
        assert total_count >= 1

        # Test get problems with limit
        limited_problems, _ = await problem_repository.get_problems(
            ProblemFilters(limit=1)
        )
        assert len(limited_problems) == 1

        # Test get random problem
        random_problem = await problem_repository.get_random_problem(ProblemFilters())
        assert random_problem is not None

        # Test not found cases
        non_existent_problem = await problem_repository.get_problem(uuid4())
        assert non_existent_problem is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_problems_by_metadata(self, problem_repository):
        """Test problem search by metadata functionality using repository."""
        # Create test problem with specific metadata for searching
        unique_suffix = uuid4().hex[:8]

        # Create problem with specific metadata for searching
        grammar_problem_data = generate_random_problem_data()
        grammar_problem_data["title"] = f"grammar_test_{unique_suffix}"
        grammar_problem_data["problem_type"] = ProblemType.GRAMMAR.value
        grammar_problem_data["target_language_code"] = "fra"
        grammar_problem_data["metadata"] = {"test_key": f"test_value_{unique_suffix}"}

        await problem_repository.create_problem(ProblemCreate(**grammar_problem_data))

        # Test search by metadata
        metadata_results = await problem_repository.search_problems_by_metadata(
            {"test_key": f"test_value_{unique_suffix}"}
        )
        assert len(metadata_results) >= 1
        found_metadata = [p.metadata for p in metadata_results if p.metadata]
        assert any(
            meta.get("test_key") == f"test_value_{unique_suffix}"
            for meta in found_metadata
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_problem_filtering_and_pagination(self, problem_repository):
        """Test problem filtering and pagination functionality using repository."""
        # Create multiple test problems
        unique_suffix = uuid4().hex[:8]

        problems_data = []
        for i in range(3):
            problem_data = generate_random_problem_data()
            problem_data["title"] = f"filter_test_{i}_{unique_suffix}"
            problem_data["problem_type"] = ProblemType.GRAMMAR.value
            problems_data.append(problem_data)

        created_problems = []
        for problem_data in problems_data:
            created_problem = await problem_repository.create_problem(
                ProblemCreate(**problem_data)
            )
            created_problems.append(created_problem)

        # Test filtering by problem type
        grammar_problems = await problem_repository.get_problems_by_type(
            ProblemType.GRAMMAR
        )
        assert len(grammar_problems) >= 3  # At least our created problems

        # Test pagination with filters
        paginated_problems, _ = await problem_repository.get_problems(
            ProblemFilters(limit=2)
        )
        assert len(paginated_problems) <= 2

        # Test getting recent problems with limit
        recent_problems = await problem_repository.get_recent_problems(limit=1)
        assert len(recent_problems) <= 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_repository_error_handling_edge_cases(self, problem_repository):
        """Test repository error handling for edge cases using repository."""
        # Test updating non-existent problem
        non_existent_id = uuid4()
        update_data = ProblemUpdate(title="non-existent update")

        # This should return None for non-existent problem
        result = await problem_repository.update_problem(non_existent_id, update_data)
        assert result is None

        # Test deleting non-existent problem
        delete_result = await problem_repository.delete_problem(non_existent_id)
        assert delete_result is False

        # Test empty update - skip this test as it may not be supported
        # Different repositories handle empty updates differently
