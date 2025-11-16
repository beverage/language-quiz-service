"""Problems repository for data access."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from postgrest import APIError as PostgrestAPIError

from src.clients.supabase import get_supabase_client
from src.core.exceptions import RepositoryError
from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemFilters,
    ProblemSummary,
    ProblemType,
    ProblemUpdate,
)
from supabase import AsyncClient

logger = logging.getLogger(__name__)


class ProblemRepository:
    """Repository for problem data access operations."""

    @classmethod
    async def create(cls, client: AsyncClient | None = None) -> "ProblemRepository":
        """Asynchronously create an instance of ProblemRepository."""
        if client is None:
            client = await get_supabase_client()
        return cls(client)

    def __init__(self, client: AsyncClient):
        """Initialize the repository with a Supabase client."""
        self.client = client

    async def create_problem(self, problem: ProblemCreate) -> Problem:
        """Create a new problem."""
        problem_dict = problem.model_dump(
            mode="json"
        )  # Use mode="json" to serialize enums correctly

        try:
            result = await self.client.table("problems").insert(problem_dict).execute()
        except PostgrestAPIError as e:
            logger.error(f"Database error creating problem: {e.message}")
            raise RepositoryError(f"Failed to create problem: {e.message}") from e

        if result.data:
            try:
                return Problem.model_validate(
                    self._prepare_problem_data(result.data[0])
                )
            except Exception as e:
                logger.error(f"Failed to validate problem data after creation: {e}")
                logger.error(f"Raw data from Supabase: {result.data[0]}")
                raise RepositoryError(
                    "Failed to validate problem data after creation"
                ) from e
        raise RepositoryError(
            "Failed to create problem: No data returned from Supabase"
        )

    async def get_problem(self, problem_id: UUID) -> Problem | None:
        """Get a problem by ID."""
        result = (
            await self.client.table("problems")
            .select("*")
            .eq("id", str(problem_id))
            .execute()
        )

        if result.data:
            return Problem.model_validate(self._prepare_problem_data(result.data[0]))
        return None

    async def get_problems(
        self, filters: ProblemFilters, include_statements: bool = True
    ) -> tuple[list[Problem], int]:
        """
        Get problems with filtering and pagination.
        Returns tuple of (problems, total_count).
        """
        # Build the select clause
        select_fields = (
            "*"
            if include_statements
            else """
            id, created_at, updated_at, problem_type, title, instructions,
            correct_answer_index, target_language_code, topic_tags,
            source_statement_ids, metadata
        """
        )

        # Start with base query
        query = self.client.table("problems").select(select_fields, count="exact")

        # Apply filters
        query = self._apply_filters(query, filters)

        # Apply pagination
        query = query.range(filters.offset, filters.offset + filters.limit - 1)

        result = await query.execute()

        problems = (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )
        total_count = result.count or 0

        return problems, total_count

    async def get_problem_summaries(
        self, filters: ProblemFilters
    ) -> tuple[list[ProblemSummary], int]:
        """Get lightweight problem summaries for list views."""
        # PostgREST approach: First get basic fields, then compute statement_count in Python
        # This avoids the PostgREST function call issue
        select_fields = """
            id, problem_type, title, instructions, correct_answer_index,
            topic_tags, created_at, statements
        """

        query = self.client.table("problems").select(select_fields, count="exact")
        query = self._apply_filters(query, filters)
        query = query.range(filters.offset, filters.offset + filters.limit - 1)

        result = await query.execute()

        summaries = []
        if result.data:
            for p in result.data:
                # Calculate statement_count in Python from the JSONB data
                statement_count = (
                    len(p.get("statements", [])) if p.get("statements") else 0
                )

                # Create summary data without the statements field (not needed for summary)
                summary_data = {
                    "id": p["id"],
                    "problem_type": p["problem_type"],
                    "title": p["title"],
                    "instructions": p["instructions"],
                    "correct_answer_index": p["correct_answer_index"],
                    "topic_tags": p["topic_tags"],
                    "created_at": p["created_at"],
                    "statement_count": statement_count,
                }
                summaries.append(ProblemSummary.model_validate(summary_data))

        return summaries, result.count or 0

    async def update_problem(
        self, problem_id: UUID, problem_data: ProblemUpdate
    ) -> Problem | None:
        """Update a problem."""
        update_dict = problem_data.model_dump(
            exclude_unset=True, mode="json"
        )  # Use mode="json" for enum serialization

        result = (
            await self.client.table("problems")
            .update(update_dict)
            .eq("id", str(problem_id))
            .execute()
        )

        if result.data:
            return Problem.model_validate(self._prepare_problem_data(result.data[0]))
        return None

    async def delete_problem(self, problem_id: UUID) -> bool:
        """Delete a problem."""
        result = (
            await self.client.table("problems")
            .delete()
            .eq("id", str(problem_id))
            .execute()
        )
        return len(result.data) > 0

    def _prepare_problem_data(self, problem_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare problem data from database for model validation."""
        # Handle null metadata from database
        if problem_data.get("metadata") is None:
            problem_data["metadata"] = {}
        return problem_data

    async def get_problems_by_type(
        self, problem_type: ProblemType, limit: int = 50
    ) -> list[Problem]:
        """Get problems by type."""
        result = (
            await self.client.table("problems")
            .select("*")
            .eq("problem_type", problem_type.value)
            .limit(limit)
            .execute()
        )
        return (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )

    async def get_problems_by_topic_tags(
        self, topic_tags: list[str], limit: int = 50
    ) -> list[Problem]:
        """Get problems that contain any of the specified topic tags."""
        # Use array overlap operator
        result = (
            await self.client.table("problems")
            .select("*")
            .or_(f"topic_tags.ov.{{{','.join(topic_tags)}}}")
            .limit(limit)
            .execute()
        )
        return (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )

    async def get_problems_using_statement(
        self, statement_id: UUID, limit: int = 50
    ) -> list[Problem]:
        """Get problems that reference a specific source statement."""
        result = (
            await self.client.table("problems")
            .select("*")
            .contains("source_statement_ids", [str(statement_id)])
            .limit(limit)
            .execute()
        )
        return (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )

    async def search_problems_by_metadata(
        self, metadata_query: dict[str, Any], limit: int = 50
    ) -> list[Problem]:
        """Search problems by metadata containment."""
        result = (
            await self.client.table("problems")
            .select("*")
            .contains("metadata", metadata_query)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )

    async def get_least_recently_served_problem(self) -> Problem | None:
        """
        Get the least recently served problem from the database.

        Returns problems that have never been served first (last_served_at IS NULL),
        then problems ordered by oldest last_served_at.

        Returns:
            Problem object if found, None if no problems exist
        """
        try:
            response = (
                await self.client.table("problems")
                .select("*")
                .order("last_served_at", desc=False, nullsfirst=True)
                .order("created_at", desc=False)  # Tiebreaker: oldest created first
                .limit(1)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                return None

            problem_data = response.data[0]
            return Problem.model_validate(self._prepare_problem_data(problem_data))

        except Exception as e:
            logger.error(f"Error fetching least recently served problem: {e}")
            raise

    async def update_problem_last_served(self, problem_id: UUID) -> bool:
        """
        Update the last_served_at timestamp for a problem.

        Args:
            problem_id: ID of the problem to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            await (
                self.client.table("problems")
                .update({"last_served_at": datetime.now(UTC).isoformat()})
                .eq("id", str(problem_id))
                .execute()
            )

            logger.debug(f"Updated last_served_at for problem {problem_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating last_served_at for problem {problem_id}: {e}")
            return False

    async def get_random_problem(
        self,
        filters: ProblemFilters,
    ) -> Problem | None:
        """Get a random problem with optional filters."""
        # Note: Supabase doesn't have native random, this is a simple implementation
        query = self.client.table("problems").select("*")

        query = self._apply_filters(query, filters)

        result = await query.limit(50).execute()

        if result.data:
            import random

            return Problem.model_validate(
                self._prepare_problem_data(random.choice(result.data))
            )
        return None

    async def count_problems(
        self,
        problem_type: ProblemType | None = None,
        topic_tags: list[str] | None = None,
    ) -> int:
        """Count problems with optional filters."""
        query = self.client.table("problems").select("id", count="exact")

        if problem_type:
            query = query.eq("problem_type", problem_type.value)

        if topic_tags:
            query = query.or_(f"topic_tags.ov.{{{','.join(topic_tags)}}}")

        result = await query.execute()
        return result.count or 0

    def _apply_filters(self, query, filters: ProblemFilters):
        """Apply filters to a Supabase query."""
        if filters.problem_type:
            query = query.eq("problem_type", filters.problem_type.value)

        if filters.target_language_code:
            query = query.eq("target_language_code", filters.target_language_code)

        if filters.topic_tags:
            # Use array overlap operator for topic tags
            query = query.or_(f"topic_tags.ov.{{{','.join(filters.topic_tags)}}}")

        if filters.created_after:
            query = query.gte("created_at", filters.created_after.isoformat())

        if filters.created_before:
            query = query.lte("created_at", filters.created_before.isoformat())

        if filters.verb:
            # Filter problems that contain the verb in metadata
            query = query.contains("metadata", {"verb_infinitive": filters.verb})

        if filters.metadata_contains:
            # Use JSONB containment operator
            query = query.contains("metadata", filters.metadata_contains)

        return query

    # Analytics and reporting methods
    async def get_problem_statistics(self) -> dict[str, Any]:
        """Get basic statistics about problems."""
        # Get total count
        total_result = (
            await self.client.table("problems").select("id", count="exact").execute()
        )
        total_count = total_result.count or 0

        # Get count by type
        type_counts = {}
        for problem_type in ProblemType:
            type_result = (
                await self.client.table("problems")
                .select("id", count="exact")
                .eq("problem_type", problem_type.value)
                .execute()
            )
            type_counts[problem_type.value] = type_result.count or 0

        return {
            "total_problems": total_count,
            "problems_by_type": type_counts,
        }

    async def get_problems_with_topic_tag(
        self, topic_tag: str, limit: int = 50
    ) -> list[Problem]:
        """Get problems that contain a specific topic tag."""
        result = (
            await self.client.table("problems")
            .select("*")
            .contains("topic_tags", [topic_tag])
            .limit(limit)
            .execute()
        )
        return (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )

    async def get_recent_problems(self, limit: int = 10) -> list[Problem]:
        """Get the most recently created problems."""
        result = (
            await self.client.table("problems")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )
