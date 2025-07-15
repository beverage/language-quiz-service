"""Problems repository for data access."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from supabase import Client

from src.clients.supabase import get_supabase_client
from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemUpdate,
    ProblemType,
    ProblemFilters,
    ProblemSummary,
)

logger = logging.getLogger(__name__)


class ProblemRepository:
    """Repository for problem data access operations."""

    @classmethod
    async def create(cls, client: Optional[Client] = None) -> "ProblemRepository":
        """Asynchronously create an instance of ProblemRepository."""
        if client is None:
            client = await get_supabase_client()
        return cls(client)

    def __init__(self, client: Client):
        """Initialize the repository with a Supabase client."""
        self.client = client

    async def create_problem(self, problem: ProblemCreate) -> Problem:
        """Create a new problem."""
        problem_dict = problem.model_dump(
            mode="json"
        )  # Use mode="json" to serialize enums correctly

        result = await self.client.table("problems").insert(problem_dict).execute()

        if result.data:
            return Problem.model_validate(self._prepare_problem_data(result.data[0]))
        raise Exception("Failed to create problem")

    async def get_problem(self, problem_id: UUID) -> Optional[Problem]:
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
    ) -> Tuple[List[Problem], int]:
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
    ) -> Tuple[List[ProblemSummary], int]:
        """Get lightweight problem summaries for list views."""
        # Select only fields needed for summary
        select_fields = """
            id, problem_type, title, instructions, correct_answer_index, 
            topic_tags, created_at, jsonb_array_length(statements) as statement_count
        """

        query = self.client.table("problems").select(select_fields, count="exact")
        query = self._apply_filters(query, filters)
        query = query.range(filters.offset, filters.offset + filters.limit - 1)

        result = await query.execute()

        summaries = []
        if result.data:
            for p in result.data:
                # ProblemSummary expects statement_count as a field
                summary_data = {**p, "statement_count": p.get("statement_count", 0)}
                summaries.append(ProblemSummary.model_validate(summary_data))

        return summaries, result.count or 0

    async def update_problem(
        self, problem_id: UUID, problem_data: ProblemUpdate
    ) -> Optional[Problem]:
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

    def _prepare_problem_data(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare problem data from database for model validation."""
        # Handle null metadata from database
        if problem_data.get("metadata") is None:
            problem_data["metadata"] = {}
        return problem_data

    async def get_problems_by_type(
        self, problem_type: ProblemType, limit: int = 50
    ) -> List[Problem]:
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
        self, topic_tags: List[str], limit: int = 50
    ) -> List[Problem]:
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
    ) -> List[Problem]:
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
        self, metadata_query: Dict[str, Any], limit: int = 50
    ) -> List[Problem]:
        """Search problems by metadata containment."""
        result = (
            await self.client.table("problems")
            .select("*")
            .contains("metadata", metadata_query)
            .limit(limit)
            .execute()
        )
        return (
            [Problem.model_validate(self._prepare_problem_data(p)) for p in result.data]
            if result.data
            else []
        )

    async def get_random_problem(
        self,
        problem_type: Optional[ProblemType] = None,
        topic_tags: Optional[List[str]] = None,
    ) -> Optional[Problem]:
        """Get a random problem with optional filters."""
        # Note: Supabase doesn't have native random, this is a simple implementation
        query = self.client.table("problems").select("*")

        if problem_type:
            query = query.eq("problem_type", problem_type.value)

        if topic_tags:
            query = query.or_(f"topic_tags.ov.{{{','.join(topic_tags)}}}")

        result = await query.limit(50).execute()

        if result.data:
            import random

            return Problem.model_validate(
                self._prepare_problem_data(random.choice(result.data))
            )
        return None

    async def count_problems(
        self,
        problem_type: Optional[ProblemType] = None,
        topic_tags: Optional[List[str]] = None,
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

        if filters.metadata_contains:
            # Use JSONB containment operator
            query = query.contains("metadata", filters.metadata_contains)

        return query

    # Analytics and reporting methods
    async def get_problem_statistics(self) -> Dict[str, Any]:
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
    ) -> List[Problem]:
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

    async def get_recent_problems(self, limit: int = 10) -> List[Problem]:
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
