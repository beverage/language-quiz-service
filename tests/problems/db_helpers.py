"""
Database helpers for problems domain tests.

Provides high-level abstractions using domain objects with automatic JSON/complex field handling.
Follows the established pattern of domain-specific helpers that can be imported across domains.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

import asyncpg

from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemUpdate,
    ProblemType,
    ProblemFilters,
)


async def create_problem(
    conn: asyncpg.Connection, problem_data: ProblemCreate
) -> Problem:
    """
    Create a problem in the database with automatic JSON conversion.

    Args:
        conn: Database connection
        problem_data: Problem data to create

    Returns:
        Created Problem instance

    Raises:
        asyncpg.ForeignKeyViolationError: If source_statement_ids reference non-existent records
        asyncpg.CheckViolationError: If data violates database constraints
    """
    problem_id = uuid4()

    query = """
        INSERT INTO problems (
            id, problem_type, title, instructions, correct_answer_index, 
            target_language_code, statements, topic_tags, source_statement_ids, metadata,
            created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11)
        RETURNING *
    """

    now = datetime.now(timezone.utc)

    result = await conn.fetchrow(
        query,
        problem_id,
        problem_data.problem_type.value,
        problem_data.title,
        problem_data.instructions,
        problem_data.correct_answer_index,
        problem_data.target_language_code,
        json.dumps(problem_data.statements),  # Auto JSON conversion
        problem_data.topic_tags,
        [
            str(sid) for sid in problem_data.source_statement_ids
        ],  # UUID array to string array
        json.dumps(problem_data.metadata) if problem_data.metadata else None,
        now,
    )

    return _row_to_problem(result)


async def get_problem(conn: asyncpg.Connection, problem_id: UUID) -> Optional[Problem]:
    """
    Get a problem by ID with automatic JSON parsing.

    Args:
        conn: Database connection
        problem_id: Problem ID to retrieve

    Returns:
        Problem instance if found, None otherwise
    """
    query = "SELECT * FROM problems WHERE id = $1"
    result = await conn.fetchrow(query, problem_id)

    return _row_to_problem(result) if result else None


async def get_problems(
    conn: asyncpg.Connection,
    filters: Optional[ProblemFilters] = None,
    include_statements: bool = True,
) -> Tuple[List[Problem], int]:
    """
    Get problems with filtering and pagination.

    Args:
        conn: Database connection
        filters: Optional filters to apply
        include_statements: Whether to include statements in results

    Returns:
        Tuple of (problems list, total count)
    """
    if filters is None:
        filters = ProblemFilters()

    # Build base query
    select_fields = (
        "*"
        if include_statements
        else """
        id, created_at, updated_at, problem_type, title, instructions, 
        correct_answer_index, target_language_code, topic_tags, 
        source_statement_ids, metadata
    """
    )

    where_conditions = []
    params = []
    param_count = 0

    # Apply filters
    if filters.problem_type:
        param_count += 1
        where_conditions.append(f"problem_type = ${param_count}")
        params.append(filters.problem_type.value)

    if filters.target_language_code:
        param_count += 1
        where_conditions.append(f"target_language_code = ${param_count}")
        params.append(filters.target_language_code)

    if filters.topic_tags:
        param_count += 1
        where_conditions.append(f"topic_tags && ${param_count}")  # Array overlap
        params.append(filters.topic_tags)

    if filters.created_after:
        param_count += 1
        where_conditions.append(f"created_at >= ${param_count}")
        params.append(filters.created_after)

    if filters.created_before:
        param_count += 1
        where_conditions.append(f"created_at <= ${param_count}")
        params.append(filters.created_before)

    if filters.metadata_contains:
        param_count += 1
        where_conditions.append(f"metadata @> ${param_count}")  # JSONB containment
        params.append(json.dumps(filters.metadata_contains))

    # Build WHERE clause
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    # Count query
    count_query = f"SELECT COUNT(*) FROM problems {where_clause}"
    total_count = await conn.fetchval(count_query, *params)

    # Data query with pagination
    data_query = f"""
        SELECT {select_fields} 
        FROM problems 
        {where_clause} 
        ORDER BY created_at DESC 
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
    """
    params.extend([filters.limit, filters.offset])

    rows = await conn.fetch(data_query, *params)
    problems = [_row_to_problem(row) for row in rows]

    return problems, total_count


async def update_problem(
    conn: asyncpg.Connection, problem_id: UUID, problem_data: ProblemUpdate
) -> Optional[Problem]:
    """
    Update a problem with automatic JSON conversion.

    Args:
        conn: Database connection
        problem_id: Problem ID to update
        problem_data: Update data

    Returns:
        Updated Problem instance if found, None otherwise

    Raises:
        asyncpg.CheckViolationError: If update violates database constraints
    """
    update_dict = problem_data.model_dump(exclude_unset=True)

    if not update_dict:
        # No fields to update, just return current problem
        return await get_problem(conn, problem_id)

    # Build dynamic update query
    set_clauses = []
    params = []
    param_count = 0

    for key, value in update_dict.items():
        param_count += 1

        if key == "problem_type" and value:
            set_clauses.append(f"problem_type = ${param_count}")
            params.append(value.value)
        elif key == "statements" and value:
            set_clauses.append(f"statements = ${param_count}")
            params.append(json.dumps(value))
        elif key == "source_statement_ids" and value:
            set_clauses.append(f"source_statement_ids = ${param_count}")
            params.append([str(sid) for sid in value])
        elif key == "metadata" and value:
            set_clauses.append(f"metadata = ${param_count}")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{key} = ${param_count}")
            params.append(value)

    # Add updated_at
    param_count += 1
    set_clauses.append(f"updated_at = ${param_count}")
    params.append(datetime.now(timezone.utc))

    # Add WHERE clause
    param_count += 1
    params.append(problem_id)

    query = f"""
        UPDATE problems 
        SET {', '.join(set_clauses)}
        WHERE id = ${param_count}
        RETURNING *
    """

    result = await conn.fetchrow(query, *params)
    return _row_to_problem(result) if result else None


async def delete_problem(conn: asyncpg.Connection, problem_id: UUID) -> bool:
    """
    Delete a problem from the database.

    Args:
        conn: Database connection
        problem_id: Problem ID to delete

    Returns:
        True if problem was deleted, False if not found
    """
    query = "DELETE FROM problems WHERE id = $1"
    result = await conn.execute(query, problem_id)

    # Parse the result string like "DELETE 1" to get affected rows
    return result.split()[-1] != "0"


async def get_problems_by_type(
    conn: asyncpg.Connection, problem_type: ProblemType, limit: int = 50
) -> List[Problem]:
    """
    Get problems by type.

    Args:
        conn: Database connection
        problem_type: Type of problems to retrieve
        limit: Maximum number of problems to return

    Returns:
        List of Problem instances
    """
    query = """
        SELECT * FROM problems 
        WHERE problem_type = $1 
        ORDER BY created_at DESC 
        LIMIT $2
    """

    rows = await conn.fetch(query, problem_type.value, limit)
    return [_row_to_problem(row) for row in rows]


async def get_problems_by_topic_tags(
    conn: asyncpg.Connection, topic_tags: List[str], limit: int = 50
) -> List[Problem]:
    """
    Get problems that contain any of the specified topic tags.

    Args:
        conn: Database connection
        topic_tags: List of topic tags to search for
        limit: Maximum number of problems to return

    Returns:
        List of Problem instances
    """
    query = """
        SELECT * FROM problems 
        WHERE topic_tags && $1 
        ORDER BY created_at DESC 
        LIMIT $2
    """

    rows = await conn.fetch(query, topic_tags, limit)
    return [_row_to_problem(row) for row in rows]


async def get_random_problem(
    conn: asyncpg.Connection,
    problem_type: Optional[ProblemType] = None,
    topic_tags: Optional[List[str]] = None,
) -> Optional[Problem]:
    """
    Get a random problem with optional filters.

    Args:
        conn: Database connection
        problem_type: Optional problem type filter
        topic_tags: Optional topic tags filter

    Returns:
        Random Problem instance if found, None otherwise
    """
    where_conditions = []
    params = []
    param_count = 0

    if problem_type:
        param_count += 1
        where_conditions.append(f"problem_type = ${param_count}")
        params.append(problem_type.value)

    if topic_tags:
        param_count += 1
        where_conditions.append(f"topic_tags && ${param_count}")
        params.append(topic_tags)

    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    # Get random problem using ORDER BY RANDOM()
    query = f"""
        SELECT * FROM problems 
        {where_clause} 
        ORDER BY RANDOM() 
        LIMIT 1
    """

    result = await conn.fetchrow(query, *params)
    return _row_to_problem(result) if result else None


async def count_problems(
    conn: asyncpg.Connection,
    problem_type: Optional[ProblemType] = None,
    topic_tags: Optional[List[str]] = None,
) -> int:
    """
    Count problems with optional filters.

    Args:
        conn: Database connection
        problem_type: Optional problem type filter
        topic_tags: Optional topic tags filter

    Returns:
        Number of matching problems
    """
    where_conditions = []
    params = []
    param_count = 0

    if problem_type:
        param_count += 1
        where_conditions.append(f"problem_type = ${param_count}")
        params.append(problem_type.value)

    if topic_tags:
        param_count += 1
        where_conditions.append(f"topic_tags && ${param_count}")
        params.append(topic_tags)

    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    query = f"SELECT COUNT(*) FROM problems {where_clause}"
    return await conn.fetchval(query, *params)


async def get_recent_problems(
    conn: asyncpg.Connection, limit: int = 10
) -> List[Problem]:
    """
    Get the most recently created problems.

    Args:
        conn: Database connection
        limit: Maximum number of problems to return

    Returns:
        List of Problem instances ordered by creation time (newest first)
    """
    query = """
        SELECT * FROM problems 
        ORDER BY created_at DESC 
        LIMIT $1
    """

    rows = await conn.fetch(query, limit)
    return [_row_to_problem(row) for row in rows]


def _row_to_problem(row: asyncpg.Record) -> Problem:
    """
    Convert database row to Problem instance with automatic JSON parsing.

    Args:
        row: Database row

    Returns:
        Problem instance
    """
    problem_dict = dict(row)

    # Parse JSON fields back to Python objects
    if problem_dict["statements"]:
        problem_dict["statements"] = json.loads(problem_dict["statements"])

    if problem_dict["metadata"]:
        problem_dict["metadata"] = json.loads(problem_dict["metadata"])
    else:
        # Set empty dict for None metadata to match schema expectations
        problem_dict["metadata"] = {}

    return Problem(**problem_dict)
