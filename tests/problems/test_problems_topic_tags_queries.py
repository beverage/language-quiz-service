"""Tests for database cleanup functionality with topic_tags."""

import pytest

from src.repositories.problem_repository import ProblemRepository
from src.schemas.problems import ProblemCreate
from tests.problems.fixtures import generate_random_problem_data


@pytest.mark.integration
class TestDatabaseCleanupWithTopicTags:
    """Test database cleanup using topic_tags for test data identification."""

    @pytest.mark.asyncio
    async def test_cleanup_query_finds_test_data_problems(self, test_supabase_client):
        """Test that Supabase query can find problems with test_data tag."""
        repo = ProblemRepository(test_supabase_client)

        # Create multiple problems with test_data tag
        test_problems = []
        for i in range(3):
            problem_data = generate_random_problem_data(
                title=f"Test problem {i}", topic_tags=["test_data", f"test_{i}"]
            )
            created = await repo.create_problem(ProblemCreate(**problem_data))
            test_problems.append(created)

        # Query using the cleanup pattern
        result = (
            await test_supabase_client.table("problems")
            .select("id, title, topic_tags")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        # Check that our 3 specific problems are present (not just >= 3 total)
        found_ids = [p["id"] for p in result.data]
        for problem in test_problems:
            assert str(problem.id) in found_ids, (
                f"Problem {problem.id} not found in query results. "
                f"Created {len(test_problems)} problems but query returned {len(result.data)} total."
            )

        # Cleanup
        for problem in test_problems:
            await repo.delete_problem(problem.id)

    @pytest.mark.asyncio
    async def test_cleanup_ignores_problems_without_test_data_tag(
        self, test_supabase_client
    ):
        """Test that cleanup doesn't find problems without test_data tag."""
        repo = ProblemRepository(test_supabase_client)

        # Create a problem WITHOUT test_data tag (override fixture behavior)
        problem_data = generate_random_problem_data(
            title="Production problem", topic_tags=["grammar", "production"]
        )
        # Remove test_data that fixture adds
        problem_data["topic_tags"] = ["grammar", "production"]

        created = await repo.create_problem(ProblemCreate(**problem_data))

        # Query for test_data problems
        result = (
            await test_supabase_client.table("problems")
            .select("id, title, topic_tags")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        # Our production problem should NOT be in results
        found_ids = [p["id"] for p in result.data]
        assert str(created.id) not in found_ids

        # Cleanup
        await repo.delete_problem(created.id)

    @pytest.mark.asyncio
    async def test_cleanup_batch_deletion(self, test_supabase_client):
        """Test batch deletion of problems with test_data tag."""
        repo = ProblemRepository(test_supabase_client)

        # Create 5 test problems
        test_problems = []
        for i in range(5):
            problem_data = generate_random_problem_data(
                title=f"Batch test {i}", topic_tags=["test_data", "batch_test"]
            )
            created = await repo.create_problem(ProblemCreate(**problem_data))
            test_problems.append(created)

        # Find all test problems
        result = (
            await test_supabase_client.table("problems")
            .select("id")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        test_ids = [p["id"] for p in result.data]
        assert len(test_ids) >= 5

        # Batch delete (simulate cleanup command)
        delete_result = (
            await test_supabase_client.table("problems")
            .delete()
            .in_("id", test_ids)
            .execute()
        )

        # Verify deletion
        assert len(delete_result.data) >= 5

        # Verify problems are gone
        for problem in test_problems:
            retrieved = await repo.get_problem(problem.id)
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_cleanup_preserves_real_problems(self, test_supabase_client):
        """Test that cleanup preserves problems without test_data tag."""
        repo = ProblemRepository(test_supabase_client)

        # Create one real problem and one test problem
        real_problem_data = generate_random_problem_data(
            title="Real problem to preserve", topic_tags=["grammar", "production"]
        )
        real_problem_data["topic_tags"] = ["grammar", "production"]  # Remove test_data
        real_problem = await repo.create_problem(ProblemCreate(**real_problem_data))

        test_problem_data = generate_random_problem_data(
            title="Test problem to delete", topic_tags=["test_data", "cleanup"]
        )
        test_problem = await repo.create_problem(ProblemCreate(**test_problem_data))

        # Query and delete only test problems
        test_result = (
            await test_supabase_client.table("problems")
            .select("id")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        test_ids = [p["id"] for p in test_result.data]

        await (
            test_supabase_client.table("problems")
            .delete()
            .in_("id", test_ids)
            .execute()
        )

        # Verify test problem is gone
        test_retrieved = await repo.get_problem(test_problem.id)
        assert test_retrieved is None

        # Verify real problem still exists
        real_retrieved = await repo.get_problem(real_problem.id)
        assert real_retrieved is not None
        assert real_retrieved.title == "Real problem to preserve"

        # Cleanup
        await repo.delete_problem(real_problem.id)

    @pytest.mark.asyncio
    async def test_cleanup_with_multiple_tags(self, test_supabase_client):
        """Test that problems with multiple tags including test_data are found."""
        repo = ProblemRepository(test_supabase_client)

        # Create problem with many tags
        problem_data = generate_random_problem_data(
            title="Multi-tag test",
            topic_tags=["test_data", "grammar", "advanced", "negation", "custom"],
        )
        created = await repo.create_problem(ProblemCreate(**problem_data))

        # Query should still find it
        result = (
            await test_supabase_client.table("problems")
            .select("id, topic_tags")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        found_ids = [p["id"] for p in result.data]
        assert str(created.id) in found_ids

        # Verify all tags were preserved
        found_problem = next(p for p in result.data if p["id"] == str(created.id))
        assert "test_data" in found_problem["topic_tags"]
        assert "grammar" in found_problem["topic_tags"]
        assert "custom" in found_problem["topic_tags"]

        # Cleanup
        await repo.delete_problem(created.id)

    @pytest.mark.asyncio
    async def test_cleanup_with_empty_tags(self, test_supabase_client):
        """Test that problems with empty topic_tags are not found by cleanup."""
        repo = ProblemRepository(test_supabase_client)

        # Create problem with empty tags
        problem_data = generate_random_problem_data(
            title="Empty tags problem", topic_tags=[]
        )
        problem_data["topic_tags"] = []  # Override fixture
        created = await repo.create_problem(ProblemCreate(**problem_data))

        # Query for test_data should not find it
        result = (
            await test_supabase_client.table("problems")
            .select("id")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        found_ids = [p["id"] for p in result.data]
        assert str(created.id) not in found_ids

        # Cleanup
        await repo.delete_problem(created.id)

    @pytest.mark.asyncio
    async def test_cleanup_case_sensitivity(self, test_supabase_client):
        """Test that tag matching is case-sensitive."""
        repo = ProblemRepository(test_supabase_client)

        # Create problems with different case tags
        lower_data = generate_random_problem_data(
            title="Lowercase test", topic_tags=["test_data"]
        )
        lower_problem = await repo.create_problem(ProblemCreate(**lower_data))

        upper_data = generate_random_problem_data(
            title="Uppercase test", topic_tags=["TEST_DATA"]
        )
        upper_data["topic_tags"] = ["TEST_DATA"]  # Override
        upper_problem = await repo.create_problem(ProblemCreate(**upper_data))

        # Query for lowercase "test_data"
        result = (
            await test_supabase_client.table("problems")
            .select("id, topic_tags")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        found_ids = [p["id"] for p in result.data]

        # Should find lowercase
        assert str(lower_problem.id) in found_ids

        # Should NOT find uppercase (case-sensitive)
        assert str(upper_problem.id) not in found_ids

        # Cleanup
        await repo.delete_problem(lower_problem.id)
        await repo.delete_problem(upper_problem.id)
