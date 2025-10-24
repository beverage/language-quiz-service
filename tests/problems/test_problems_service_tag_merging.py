"""Tests for topic_tags merging in ProblemService."""

import pytest

from src.repositories.problem_repository import ProblemRepository
from src.schemas.problems import ProblemCreate
from src.services.problem_service import ProblemService
from tests.problems.fixtures import generate_random_problem_data


@pytest.mark.asyncio
@pytest.mark.integration
class TestProblemServiceTagMerging:
    """Test tag merging functionality in ProblemService through problem creation."""

    async def test_fixture_always_adds_test_data_tag(self, test_supabase_client):
        """Test that generate_random_problem_data fixture always adds test_data tag."""
        # Generate problem data
        problem_data = generate_random_problem_data()

        # Verify test_data tag is present
        assert "test_data" in problem_data["topic_tags"]

        # Create the problem
        repo = ProblemRepository(test_supabase_client)
        service = ProblemService(problem_repository=repo)
        problem = await service.create_problem(ProblemCreate(**problem_data))

        assert "test_data" in problem.topic_tags

    async def test_additional_tags_preserved_in_fixture(self, test_supabase_client):
        """Test that additional tags are preserved alongside test_data."""
        # Generate problem data with custom tags
        problem_data = generate_random_problem_data(
            topic_tags=["custom_tag", "advanced"]
        )

        # Both test_data and custom tags should be present
        assert "test_data" in problem_data["topic_tags"]
        assert "custom_tag" in problem_data["topic_tags"]
        assert "advanced" in problem_data["topic_tags"]

        # Create and verify
        repo = ProblemRepository(test_supabase_client)
        service = ProblemService(problem_repository=repo)
        problem = await service.create_problem(ProblemCreate(**problem_data))

        assert "test_data" in problem.topic_tags
        assert "custom_tag" in problem.topic_tags
        assert "advanced" in problem.topic_tags

    async def test_empty_tags_list_gets_test_data(self, test_supabase_client):
        """Test that even empty topic_tags gets test_data tag added."""
        # Generate problem data with explicitly empty tags
        problem_data = generate_random_problem_data(topic_tags=[])

        # Fixture should have added test_data
        assert "test_data" in problem_data["topic_tags"]

        # Create and verify
        repo = ProblemRepository(test_supabase_client)
        service = ProblemService(problem_repository=repo)
        problem = await service.create_problem(ProblemCreate(**problem_data))

        assert "test_data" in problem.topic_tags

    async def test_duplicate_test_data_tag_handled(self, test_supabase_client):
        """Test that duplicate test_data tags don't cause issues."""
        # Generate problem data with test_data already in tags
        problem_data = generate_random_problem_data(topic_tags=["test_data", "grammar"])

        # Should have test_data (may appear twice, that's OK)
        assert "test_data" in problem_data["topic_tags"]

        # Create and verify - should not crash
        repo = ProblemRepository(test_supabase_client)
        service = ProblemService(problem_repository=repo)
        problem = await service.create_problem(ProblemCreate(**problem_data))

        assert problem.id is not None
        assert "test_data" in problem.topic_tags

    async def test_tag_ordering_test_data_first(self, test_supabase_client):
        """Test that test_data tag appears first when added by fixture."""
        # Generate problem data with custom tags
        problem_data = generate_random_problem_data(
            topic_tags=["z_last_tag", "grammar"]
        )

        # test_data should be first (prepended by fixture)
        topic_tags = problem_data["topic_tags"]
        assert topic_tags[0] == "test_data"
        assert "z_last_tag" in topic_tags
        assert "grammar" in topic_tags

        # Create and verify
        repo = ProblemRepository(test_supabase_client)
        service = ProblemService(problem_repository=repo)
        problem = await service.create_problem(ProblemCreate(**problem_data))

        # test_data should still be first
        assert problem.topic_tags[0] == "test_data"
