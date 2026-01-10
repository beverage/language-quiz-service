"""Test cases for problem repository using Supabase client only."""

from uuid import uuid4

import pytest

from src.core.exceptions import RepositoryError
from src.schemas.problems import (
    GrammarFocus,
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

        problem_title = uuid4().hex[:8]

        # Then update it
        update_data = ProblemUpdate(title=problem_title)
        result = await problem_repository.update_problem(
            created_problem.id, update_data
        )

        assert result is not None
        assert result.title == problem_title
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

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_problems_by_topic_tag(
        self, problem_repository, test_supabase_client
    ):
        """Test that problems can be queried by topic_tags."""
        # Create a problem with test_data tag
        problem_data = generate_random_problem_data(
            title="Topic tag test problem", topic_tags=["test_data", "query_test"]
        )
        created = await problem_repository.create_problem(ProblemCreate(**problem_data))

        try:
            # Query for problems with test_data tag
            result = (
                await test_supabase_client.table("problems")
                .select("id, title, topic_tags")
                .contains("topic_tags", ["test_data"])
                .execute()
            )

            assert len(result.data) > 0
            assert any(p["id"] == str(created.id) for p in result.data)
        finally:
            # Cleanup
            await problem_repository.delete_problem(created.id)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_topic_tags_filter_excludes_non_matching(
        self, problem_repository, test_supabase_client
    ):
        """Test that topic_tags query doesn't return non-matching problems."""
        # Create a problem WITHOUT test_data tag
        problem_data = generate_random_problem_data(
            title="Non-test problem",
            topic_tags=["grammar", "production"],  # No test_data
        )
        # Override the automatic test_data addition
        problem_data["topic_tags"] = ["grammar", "production"]

        created = await problem_repository.create_problem(ProblemCreate(**problem_data))

        try:
            # Query for problems with test_data tag
            result = (
                await test_supabase_client.table("problems")
                .select("id, title, topic_tags")
                .contains("topic_tags", ["test_data"])
                .execute()
            )

            # This problem should NOT be in the results
            assert not any(p["id"] == str(created.id) for p in result.data)
        finally:
            # Cleanup
            await problem_repository.delete_problem(created.id)


@pytest.mark.integration
class TestWeightedRandomProblemSelection:
    """Test cases for weighted random problem selection."""

    @pytest.mark.asyncio
    async def test_get_weighted_random_problem_returns_problem(
        self, problem_repository
    ):
        """Test that get_weighted_random_problem returns a problem when one exists."""
        # Create a test problem
        problem_data = generate_random_problem_data(focus="conjugation")
        created = await problem_repository.create_problem(ProblemCreate(**problem_data))

        try:
            result = await problem_repository.get_weighted_random_problem()
            assert result is not None
            assert isinstance(result, Problem)
        finally:
            await problem_repository.delete_problem(created.id)

    @pytest.mark.asyncio
    async def test_get_weighted_random_problem_with_focus_filter(
        self, problem_repository
    ):
        """Test that focus filter returns problems with matching grammatical_focus."""
        # Create problems with different focus values to ensure at least one exists
        conjugation_data = generate_random_problem_data(
            title=f"conjugation_test_{uuid4().hex[:8]}",
            focus="conjugation",
        )
        pronouns_data = generate_random_problem_data(
            title=f"pronouns_test_{uuid4().hex[:8]}",
            focus="pronouns",
        )

        conjugation_problem = await problem_repository.create_problem(
            ProblemCreate(**conjugation_data)
        )
        pronouns_problem = await problem_repository.create_problem(
            ProblemCreate(**pronouns_data)
        )

        try:
            # Filter by conjugation focus - should return ANY conjugation problem
            filters = ProblemFilters(focus=GrammarFocus.CONJUGATION)
            result = await problem_repository.get_weighted_random_problem(
                filters=filters
            )

            assert result is not None
            # Verify the result has conjugation focus in metadata
            assert result.metadata is not None
            assert "grammatical_focus" in result.metadata
            assert "conjugation" in result.metadata["grammatical_focus"]

            # Filter by pronouns focus - should return ANY pronouns problem
            filters = ProblemFilters(focus=GrammarFocus.PRONOUNS)
            result = await problem_repository.get_weighted_random_problem(
                filters=filters
            )

            assert result is not None
            assert result.metadata is not None
            assert "grammatical_focus" in result.metadata
            assert "pronouns" in result.metadata["grammatical_focus"]

        finally:
            await problem_repository.delete_problem(conjugation_problem.id)
            await problem_repository.delete_problem(pronouns_problem.id)

    @pytest.mark.asyncio
    async def test_get_weighted_random_problem_no_match_returns_none(
        self, problem_repository
    ):
        """Test that get_weighted_random_problem returns None when no problems match."""
        # Create a conjugation problem only
        problem_data = generate_random_problem_data(
            title=f"conjugation_only_{uuid4().hex[:8]}",
            focus="conjugation",
        )
        created = await problem_repository.create_problem(ProblemCreate(**problem_data))

        try:
            # Try to get a pronouns problem when none exist (except test data)
            # First, let's use a very specific filter that won't match
            filters = ProblemFilters(
                focus=GrammarFocus.PRONOUNS,
                target_language_code="zzz",  # Non-existent language
            )
            result = await problem_repository.get_weighted_random_problem(
                filters=filters
            )
            assert result is None
        finally:
            await problem_repository.delete_problem(created.id)

    @pytest.mark.asyncio
    async def test_get_weighted_random_problem_with_problem_type_filter(
        self, problem_repository
    ):
        """Test that problem_type filter works correctly."""
        problem_data = generate_random_problem_data(
            title=f"grammar_type_test_{uuid4().hex[:8]}",
            problem_type=ProblemType.GRAMMAR.value,
        )
        created = await problem_repository.create_problem(ProblemCreate(**problem_data))

        try:
            filters = ProblemFilters(problem_type=ProblemType.GRAMMAR)
            result = await problem_repository.get_weighted_random_problem(
                filters=filters
            )

            assert result is not None
            assert result.problem_type == ProblemType.GRAMMAR
        finally:
            await problem_repository.delete_problem(created.id)

    @pytest.mark.asyncio
    async def test_get_weighted_random_problem_accepts_virtual_staleness(
        self, problem_repository
    ):
        """Test that virtual_staleness_days parameter is accepted."""
        problem_data = generate_random_problem_data()
        created = await problem_repository.create_problem(ProblemCreate(**problem_data))

        try:
            # Just verify the parameter is accepted without error
            result = await problem_repository.get_weighted_random_problem(
                virtual_staleness_days=5.0
            )
            assert result is not None
        finally:
            await problem_repository.delete_problem(created.id)

    @pytest.mark.asyncio
    async def test_update_problem_last_served(self, problem_repository):
        """Test that update_problem_last_served updates the timestamp."""
        problem_data = generate_random_problem_data()
        created = await problem_repository.create_problem(ProblemCreate(**problem_data))

        try:
            # Initially, last_served_at should be None
            assert created.last_served_at is None

            # Update last_served_at
            result = await problem_repository.update_problem_last_served(created.id)
            assert result is True

            # Fetch the problem and verify last_served_at is set
            updated = await problem_repository.get_problem(created.id)
            assert updated.last_served_at is not None
        finally:
            await problem_repository.delete_problem(created.id)
