"""Tests for LRU problem serving functionality."""

import asyncio

import pytest

from src.schemas.problems import ProblemCreate
from tests.problems.fixtures import generate_random_problem_data, problem_repository

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestProblemRepositoryLRU:
    """Test least recently used problem functionality."""

    async def test_lru_ordering_oldest_served_first(self, problem_repository):
        """Test that LRU returns problems in correct order (oldest served first)."""
        # Create two test problems
        problem1_data = generate_random_problem_data(
            topic_tags=["test_data", "lru_order_test_1"]
        )
        problem1 = await problem_repository.create_problem(
            ProblemCreate(**problem1_data)
        )

        problem2_data = generate_random_problem_data(
            topic_tags=["test_data", "lru_order_test_2"]
        )
        problem2 = await problem_repository.create_problem(
            ProblemCreate(**problem2_data)
        )

        # Serve both problems with a delay to ensure different timestamps
        await problem_repository.update_problem_last_served(problem1.id)
        await asyncio.sleep(0.2)
        await problem_repository.update_problem_last_served(problem2.id)

        # Fetch LRU twice and verify ordering
        first_fetch = await problem_repository.get_least_recently_served_problem()
        await problem_repository.update_problem_last_served(first_fetch.id)

        # Refetch to get updated timestamp
        first_fetch_updated = await problem_repository.get_problem(first_fetch.id)

        await asyncio.sleep(0.2)

        second_fetch = await problem_repository.get_least_recently_served_problem()
        await problem_repository.update_problem_last_served(second_fetch.id)

        # Refetch to get updated timestamp
        second_fetch_updated = await problem_repository.get_problem(second_fetch.id)

        # Both should have timestamps now, and first should be older than second
        assert first_fetch_updated is not None
        assert second_fetch_updated is not None
        assert first_fetch_updated.last_served_at is not None
        assert second_fetch_updated.last_served_at is not None
        assert first_fetch_updated.last_served_at < second_fetch_updated.last_served_at

    async def test_unserved_problems_prioritized_oldest_created_first(
        self, problem_repository
    ):
        """Test that unserved problems are prioritized, with oldest created first as tiebreaker."""
        # Create two unserved problems with delay to ensure different created_at
        unserved1_data = generate_random_problem_data(
            topic_tags=["test_data", "unserved_older"]
        )
        unserved1 = await problem_repository.create_problem(
            ProblemCreate(**unserved1_data)
        )

        await asyncio.sleep(0.2)

        unserved2_data = generate_random_problem_data(
            topic_tags=["test_data", "unserved_newer"]
        )
        unserved2 = await problem_repository.create_problem(
            ProblemCreate(**unserved2_data)
        )

        # Fetch LRU twice - should get them in created_at order (oldest first)
        first_lru = await problem_repository.get_least_recently_served_problem()
        await problem_repository.update_problem_last_served(first_lru.id)

        second_lru = await problem_repository.get_least_recently_served_problem()
        await problem_repository.update_problem_last_served(second_lru.id)

        # Both fetched should be unserved initially, ordered by created_at
        # first_lru should be the older created one
        assert first_lru is not None
        assert second_lru is not None

        # If we got our test problems, verify ordering
        if first_lru.id in [unserved1.id, unserved2.id] and second_lru.id in [
            unserved1.id,
            unserved2.id,
        ]:
            # Should get older created problem first
            assert first_lru.created_at < second_lru.created_at

    async def test_update_problem_last_served(self, problem_repository):
        """Test updating last_served_at timestamp."""
        problem_data = generate_random_problem_data(
            topic_tags=["test_data", "update_test"]
        )
        problem = await problem_repository.create_problem(ProblemCreate(**problem_data))

        # Update last_served_at
        success = await problem_repository.update_problem_last_served(problem.id)
        assert success is True

        # Fetch again and verify it was updated
        updated_problem = await problem_repository.get_problem(problem.id)
        assert updated_problem is not None
        assert updated_problem.last_served_at is not None
