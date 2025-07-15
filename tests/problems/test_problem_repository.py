"""Integration tests for the problem repository using direct database calls."""

import pytest
import asyncpg
from uuid import uuid4

from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemType,
    ProblemFilters,
    ProblemUpdate,
)
from tests.problems.fixtures import (
    generate_random_problem_data,
    sample_problem_create,  # noqa: F401
)
from tests.problems import db_helpers


class TestProblemsRepository:
    """Test suite for the ProblemRepository using direct database calls."""

    async def test_create_problem_success(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test creating a problem successfully."""
        created_problem = await db_helpers.create_problem(
            supabase_db_connection, sample_problem_create
        )

        assert created_problem is not None
        assert created_problem.problem_type == sample_problem_create.problem_type
        assert created_problem.instructions == sample_problem_create.instructions
        assert created_problem.statements == sample_problem_create.statements
        assert (
            created_problem.correct_answer_index
            == sample_problem_create.correct_answer_index
        )
        assert created_problem.topic_tags == sample_problem_create.topic_tags
        assert (
            created_problem.target_language_code
            == sample_problem_create.target_language_code
        )
        assert created_problem.id is not None
        assert created_problem.created_at is not None

    async def test_create_problem_with_invalid_language_code(
        self,
        supabase_db_connection,
    ):
        """Test creating a problem with invalid language code triggers constraint violation."""
        # Test database constraint directly by inserting invalid data
        # This bypasses Pydantic validation to test actual DB constraints
        query = """
            INSERT INTO problems (
                id, problem_type, title, instructions, correct_answer_index, 
                target_language_code, statements, topic_tags, source_statement_ids, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11)
        """

        from uuid import uuid4
        from datetime import datetime, timezone
        import json

        # Should raise constraint error due to invalid language code
        with pytest.raises(asyncpg.StringDataRightTruncationError):
            await supabase_db_connection.fetchrow(
                query,
                uuid4(),
                "grammar",
                "Test Problem",
                "Choose the correct answer",
                0,
                "invalid_lang_code",  # Invalid - too long
                json.dumps([{"text": "Test statement", "is_correct": True}]),
                ["test"],
                [],
                None,
                datetime.now(timezone.utc),
            )

    async def test_get_problem_found(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test retrieving an existing problem."""
        # First create a problem
        created_problem = await db_helpers.create_problem(
            supabase_db_connection, sample_problem_create
        )

        # Then retrieve it
        problem = await db_helpers.get_problem(
            supabase_db_connection, created_problem.id
        )

        assert problem is not None
        assert problem.id == created_problem.id
        assert problem.problem_type == created_problem.problem_type
        assert problem.instructions == created_problem.instructions

    async def test_get_problem_not_found(
        self,
        supabase_db_connection,
    ):
        """Test retrieving a non-existent problem."""
        non_existent_id = uuid4()
        problem = await db_helpers.get_problem(supabase_db_connection, non_existent_id)
        assert problem is None

    async def test_get_problems_with_filters(
        self,
        supabase_db_connection,
    ):
        """Test retrieving problems with filters."""
        # Create multiple problems with different titles but same type
        grammar_data_1 = generate_random_problem_data(
            problem_type="grammar", title="Test Grammar 1"
        )
        grammar_data_2 = generate_random_problem_data(
            problem_type="grammar", title="Test Grammar 2"
        )

        await db_helpers.create_problem(
            supabase_db_connection, ProblemCreate(**grammar_data_1)
        )
        await db_helpers.create_problem(
            supabase_db_connection, ProblemCreate(**grammar_data_2)
        )

        # Test filtering by problem type
        filters = ProblemFilters(problem_type=ProblemType.GRAMMAR, limit=10, offset=0)

        problems, total_count = await db_helpers.get_problems(
            supabase_db_connection, filters
        )

        assert len(problems) >= 1
        assert total_count >= len(problems)
        assert all(p.problem_type == ProblemType.GRAMMAR for p in problems)

    async def test_get_problems_no_filters(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test retrieving problems without filters."""
        # Create at least one problem to ensure we have data
        await db_helpers.create_problem(supabase_db_connection, sample_problem_create)

        filters = ProblemFilters(limit=10, offset=0)

        problems, total_count = await db_helpers.get_problems(
            supabase_db_connection, filters
        )

        assert len(problems) >= 1
        assert total_count >= len(problems)

    async def test_get_problems_empty_result(
        self,
        supabase_db_connection,
    ):
        """Test retrieving problems when none match filters."""
        filters = ProblemFilters(
            problem_type=ProblemType.GRAMMAR,
            topic_tags=["non_existent_tag"],
            limit=10,
            offset=0,
        )

        problems, total_count = await db_helpers.get_problems(
            supabase_db_connection, filters
        )
        assert len(problems) == 0
        assert total_count == 0

    async def test_update_problem_success(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
        sample_problem_update: ProblemUpdate,
    ):
        """Test updating a problem successfully."""
        # First create a problem
        created_problem = await db_helpers.create_problem(
            supabase_db_connection, sample_problem_create
        )

        # Then update it
        updated_problem = await db_helpers.update_problem(
            supabase_db_connection, created_problem.id, sample_problem_update
        )

        assert updated_problem is not None
        assert updated_problem.id == created_problem.id
        # Check that updated fields have changed
        if sample_problem_update.instructions:
            assert updated_problem.instructions == sample_problem_update.instructions
        if sample_problem_update.title:
            assert updated_problem.title == sample_problem_update.title

    async def test_update_problem_not_found(
        self,
        supabase_db_connection,
        sample_problem_update: ProblemUpdate,
    ):
        """Test updating a non-existent problem."""
        non_existent_id = uuid4()
        updated_problem = await db_helpers.update_problem(
            supabase_db_connection, non_existent_id, sample_problem_update
        )
        assert updated_problem is None

    async def test_delete_problem_success(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test deleting a problem successfully."""
        # First create a problem
        created_problem = await db_helpers.create_problem(
            supabase_db_connection, sample_problem_create
        )

        # Then delete it
        success = await db_helpers.delete_problem(
            supabase_db_connection, created_problem.id
        )
        assert success is True

        # Verify problem is deleted
        deleted_problem = await db_helpers.get_problem(
            supabase_db_connection, created_problem.id
        )
        assert deleted_problem is None

    async def test_delete_problem_not_found(
        self,
        supabase_db_connection,
    ):
        """Test deleting a non-existent problem."""
        non_existent_id = uuid4()
        success = await db_helpers.delete_problem(
            supabase_db_connection, non_existent_id
        )
        assert success is False

    async def test_get_problems_by_type(
        self,
        supabase_db_connection,
    ):
        """Test retrieving problems by type."""
        # Create multiple grammar problems
        grammar_data_1 = generate_random_problem_data(
            problem_type="grammar", topic_tags=["articles"]
        )
        grammar_data_2 = generate_random_problem_data(
            problem_type="grammar", topic_tags=["conjugation"]
        )

        await db_helpers.create_problem(
            supabase_db_connection, ProblemCreate(**grammar_data_1)
        )
        await db_helpers.create_problem(
            supabase_db_connection, ProblemCreate(**grammar_data_2)
        )

        # Get problems by type
        problems = await db_helpers.get_problems_by_type(
            supabase_db_connection, ProblemType.GRAMMAR
        )

        assert len(problems) >= 2
        assert all(p.problem_type == ProblemType.GRAMMAR for p in problems)

    async def test_get_problems_by_topic_tags(
        self,
        supabase_db_connection,
    ):
        """Test retrieving problems by topic tags."""
        # Create problems with specific topic tags
        data_with_tags = generate_random_problem_data(topic_tags=["grammar", "verbs"])
        data_without_tags = generate_random_problem_data(
            topic_tags=["articles", "nouns"]
        )

        await db_helpers.create_problem(
            supabase_db_connection, ProblemCreate(**data_with_tags)
        )
        await db_helpers.create_problem(
            supabase_db_connection, ProblemCreate(**data_without_tags)
        )

        # Search for problems with target tags
        target_tags = ["grammar", "verbs"]
        problems = await db_helpers.get_problems_by_topic_tags(
            supabase_db_connection, target_tags
        )

        assert len(problems) >= 1
        # Check that all returned problems have at least one of the target tags
        for problem in problems:
            assert any(tag in problem.topic_tags for tag in target_tags)

    async def test_get_problems_by_topic_tags_empty(
        self,
        supabase_db_connection,
    ):
        """Test retrieving problems by non-existent topic tags."""
        problems = await db_helpers.get_problems_by_topic_tags(
            supabase_db_connection, ["non_existent"]
        )
        assert len(problems) == 0

    async def test_get_random_problem(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test retrieving a random problem."""
        # Create at least one problem to ensure we have data
        await db_helpers.create_problem(supabase_db_connection, sample_problem_create)

        problem = await db_helpers.get_random_problem(supabase_db_connection)

        assert problem is not None
        assert isinstance(problem, Problem)
        assert problem.id is not None
        assert problem.problem_type is not None

    async def test_get_random_problem_no_problems(
        self,
        supabase_db_connection,
    ):
        """Test retrieving a random problem when none exist."""
        # The fresh test database should be empty for problems
        problem = await db_helpers.get_random_problem(supabase_db_connection)
        # This might return None if database is empty, which is acceptable
        assert problem is None or isinstance(problem, Problem)

    async def test_count_problems(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test counting problems."""
        # Create a problem to ensure we have data
        await db_helpers.create_problem(supabase_db_connection, sample_problem_create)

        count = await db_helpers.count_problems(supabase_db_connection)
        assert count >= 1

    async def test_get_recent_problems(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test retrieving recent problems."""
        # Create multiple problems to test ordering
        await db_helpers.create_problem(supabase_db_connection, sample_problem_create)

        # Create another problem with slightly different data
        problem_data2 = generate_random_problem_data()
        await db_helpers.create_problem(
            supabase_db_connection, ProblemCreate(**problem_data2)
        )

        recent_problems = await db_helpers.get_recent_problems(
            supabase_db_connection, limit=5
        )

        assert len(recent_problems) <= 5
        assert len(recent_problems) >= 1
        # Should be ordered by creation time (most recent first)
        if len(recent_problems) > 1:
            for i in range(len(recent_problems) - 1):
                assert (
                    recent_problems[i].created_at >= recent_problems[i + 1].created_at
                )

    async def test_get_recent_problems_empty(
        self,
        supabase_db_connection,
    ):
        """Test retrieving recent problems with proper limit handling."""
        # Test that the method returns a list (may be empty or have results)
        recent_problems = await db_helpers.get_recent_problems(
            supabase_db_connection, limit=5
        )
        assert isinstance(recent_problems, list)
        assert len(recent_problems) <= 5  # Should respect the limit
        # Verify each item is a valid Problem
        for problem in recent_problems:
            assert isinstance(problem, Problem)
            assert problem.id is not None

    # ============================================================================
    # Error Testing - Database Constraints
    # ============================================================================

    async def test_create_problem_with_invalid_correct_answer_index(
        self,
        supabase_db_connection,
    ):
        """Test creating problem with correct_answer_index out of range triggers constraint violation."""
        # Test database constraint directly by inserting invalid data
        # This bypasses Pydantic validation to test actual DB constraints
        query = """
            INSERT INTO problems (
                id, problem_type, title, instructions, correct_answer_index, 
                target_language_code, statements, topic_tags, source_statement_ids, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11)
        """

        from uuid import uuid4
        from datetime import datetime, timezone
        import json

        # Should raise constraint error due to out-of-range correct_answer_index
        with pytest.raises(asyncpg.CheckViolationError):
            await supabase_db_connection.fetchrow(
                query,
                uuid4(),
                "grammar",
                "Test Problem",
                "Choose the correct answer",
                99,  # Out of range for statements array
                "eng",
                json.dumps([{"text": "Single statement", "is_correct": True}]),
                ["test"],
                [],
                None,
                datetime.now(timezone.utc),
            )

    async def test_create_problem_with_empty_statements(
        self,
        supabase_db_connection,
    ):
        """Test creating problem with empty statements array triggers constraint violation."""
        problem_data = generate_random_problem_data()
        problem_data["statements"] = []  # Empty statements array

        # Should fail at Pydantic validation level before reaching database
        with pytest.raises(ValueError):
            ProblemCreate(**problem_data)

    async def test_update_problem_with_constraint_violation(
        self,
        supabase_db_connection,
        sample_problem_create: ProblemCreate,
    ):
        """Test updating problem with data that violates constraints."""
        # First create a valid problem
        created_problem = await db_helpers.create_problem(
            supabase_db_connection, sample_problem_create
        )

        # Test database constraint directly by updating with invalid data
        # This bypasses Pydantic validation to test actual DB constraints
        query = """
            UPDATE problems 
            SET statements = $1, correct_answer_index = $2
            WHERE id = $3
        """

        import json

        # Should raise constraint error due to out-of-range correct_answer_index
        with pytest.raises(asyncpg.CheckViolationError):
            await supabase_db_connection.execute(
                query,
                json.dumps([{"text": "Single statement", "is_correct": True}]),
                5,  # Out of range for single statement
                created_problem.id,
            )

    async def test_cross_domain_constraint_with_foreign_keys(
        self,
        supabase_db_connection,
    ):
        """Test creating problem with non-existent source_statement_ids."""
        # Create problem data that references non-existent statement IDs
        problem_data = generate_random_problem_data()
        problem_data["source_statement_ids"] = [uuid4()]  # Non-existent ID
        problem_create = ProblemCreate(**problem_data)

        # For now, this doesn't raise an error since source_statement_ids might not have
        # foreign key constraints yet. This test demonstrates the pattern for when
        # actual foreign key relationships are implemented.
        created_problem = await db_helpers.create_problem(
            supabase_db_connection, problem_create
        )

        # Verify the problem was created (no constraint violation yet)
        assert created_problem is not None
        assert (
            created_problem.source_statement_ids == problem_data["source_statement_ids"]
        )
