"""Generation requests repository for data access."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from postgrest import APIError as PostgrestAPIError

from src.core.exceptions import RepositoryError
from src.schemas.generation_requests import (
    GenerationRequest,
    GenerationRequestCreate,
    GenerationStatus,
)
from supabase import AsyncClient

logger = logging.getLogger(__name__)


class GenerationRequestRepository:
    """Repository for generation request data access operations."""

    def __init__(self, client: AsyncClient):
        """Initialize the repository with a Supabase client."""
        self.client = client

    async def create_generation_request(
        self,
        request: GenerationRequestCreate,
        requested_at: datetime | None = None,
    ) -> GenerationRequest:
        """
        Create a new generation request.

        Args:
            request: The generation request data to create
            requested_at: Optional timestamp to set for requested_at.
                          If None, uses database default (NOW()).
                          Useful for testing and management tooling.

        Returns:
            The created GenerationRequest
        """
        request_dict = request.model_dump(mode="json")

        # Override requested_at if provided (useful for testing/managing old requests)
        if requested_at is not None:
            request_dict["requested_at"] = requested_at.isoformat()

        try:
            result = (
                await self.client.table("generation_requests")
                .insert(request_dict)
                .execute()
            )
        except PostgrestAPIError as e:
            logger.error(f"Database error creating generation request: {e.message}")
            raise RepositoryError(
                f"Failed to create generation request: {e.message}"
            ) from e

        if result.data:
            try:
                return GenerationRequest.model_validate(result.data[0])
            except Exception as e:
                logger.error(
                    f"Failed to validate generation request data after creation: {e}"
                )
                logger.error(f"Raw data from Supabase: {result.data[0]}")
                raise RepositoryError(
                    "Failed to validate generation request data after creation"
                ) from e
        raise RepositoryError(
            "Failed to create generation request: No data returned from Supabase"
        )

    async def get_generation_request(
        self, request_id: UUID
    ) -> GenerationRequest | None:
        """Get a generation request by ID."""
        try:
            result = (
                await self.client.table("generation_requests")
                .select("*")
                .eq("id", str(request_id))
                .execute()
            )

            if result.data:
                return GenerationRequest.model_validate(result.data[0])
            return None
        except PostgrestAPIError as e:
            logger.error(f"Database error getting generation request: {e.message}")
            raise RepositoryError(
                f"Failed to get generation request: {e.message}"
            ) from e

    async def get_problems_by_request_id(self, request_id: UUID) -> list[dict]:
        """
        Get all problems associated with a generation request.

        Returns raw problem data from database.
        """
        try:
            result = (
                await self.client.table("problems")
                .select("*")
                .eq("generation_request_id", str(request_id))
                .execute()
            )

            return result.data if result.data else []
        except PostgrestAPIError as e:
            logger.error(f"Database error getting problems by request_id: {e.message}")
            raise RepositoryError(
                f"Failed to get problems by request_id: {e.message}"
            ) from e

    async def update_status_to_processing(
        self, request_id: UUID, started_at: datetime | None = None
    ) -> GenerationRequest | None:
        """
        Update generation request status to 'processing' and set started_at.

        Only updates if current status is 'pending' to avoid race conditions.
        """
        if started_at is None:
            started_at = datetime.now(UTC)

        try:
            result = (
                await self.client.table("generation_requests")
                .update(
                    {
                        "status": GenerationStatus.PROCESSING.value,
                        "started_at": started_at.isoformat(),
                    }
                )
                .eq("id", str(request_id))
                .eq("status", GenerationStatus.PENDING.value)  # Only if still pending
                .execute()
            )

            if result.data:
                return GenerationRequest.model_validate(result.data[0])
            return None
        except PostgrestAPIError as e:
            logger.error(f"Database error updating status to processing: {e.message}")
            raise RepositoryError(
                f"Failed to update status to processing: {e.message}"
            ) from e

    async def increment_generated_count(
        self, request_id: UUID
    ) -> GenerationRequest | None:
        """Increment the generated_count for a generation request."""
        try:
            # Get current request to increment
            current = await self.get_generation_request(request_id)
            if not current:
                logger.warning(
                    f"Generation request {request_id} not found for increment"
                )
                return None

            new_count = current.generated_count + 1

            result = (
                await self.client.table("generation_requests")
                .update({"generated_count": new_count})
                .eq("id", str(request_id))
                .execute()
            )

            if result.data:
                return GenerationRequest.model_validate(result.data[0])
            return None
        except PostgrestAPIError as e:
            logger.error(f"Database error incrementing generated_count: {e.message}")
            raise RepositoryError(
                f"Failed to increment generated_count: {e.message}"
            ) from e

    async def increment_failed_count(
        self, request_id: UUID, error_message: str | None = None
    ) -> GenerationRequest | None:
        """Increment the failed_count and optionally record error_message."""
        try:
            # Get current request to increment
            current = await self.get_generation_request(request_id)
            if not current:
                logger.warning(
                    f"Generation request {request_id} not found for increment"
                )
                return None

            new_count = current.failed_count + 1
            update_data = {"failed_count": new_count}

            # Append error message if provided
            if error_message:
                update_data["error_message"] = error_message

            result = (
                await self.client.table("generation_requests")
                .update(update_data)
                .eq("id", str(request_id))
                .execute()
            )

            if result.data:
                return GenerationRequest.model_validate(result.data[0])
            return None
        except PostgrestAPIError as e:
            logger.error(f"Database error incrementing failed_count: {e.message}")
            raise RepositoryError(
                f"Failed to increment failed_count: {e.message}"
            ) from e

    async def update_final_status(
        self,
        request_id: UUID,
        status: GenerationStatus,
        completed_at: datetime | None = None,
    ) -> GenerationRequest | None:
        """
        Update generation request final status and set completed_at timestamp.

        Args:
            request_id: ID of the generation request
            status: Final status (completed, partial, or failed)
            completed_at: Completion timestamp (defaults to now)
        """
        if completed_at is None:
            completed_at = datetime.now(UTC)

        try:
            result = (
                await self.client.table("generation_requests")
                .update(
                    {
                        "status": status.value,
                        "completed_at": completed_at.isoformat(),
                    }
                )
                .eq("id", str(request_id))
                .execute()
            )

            if result.data:
                return GenerationRequest.model_validate(result.data[0])
            return None
        except PostgrestAPIError as e:
            logger.error(f"Database error updating final status: {e.message}")
            raise RepositoryError(f"Failed to update final status: {e.message}") from e

    async def get_all_requests(
        self,
        status: GenerationStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[GenerationRequest], int]:
        """
        Get all generation requests with optional status filtering.

        Args:
            status: Optional status filter
            limit: Maximum number of requests to return
            offset: Number of requests to skip

        Returns:
            Tuple of (list of requests, total count)
        """
        try:
            query = self.client.table("generation_requests").select("*", count="exact")

            if status:
                query = query.eq("status", status.value)

            query = (
                query.order("requested_at", desc=True)
                .order("id", desc=True)
                .range(offset, offset + limit - 1)
            )

            result = await query.execute()

            requests = [
                GenerationRequest.model_validate(row) for row in (result.data or [])
            ]
            total_count = result.count if result.count is not None else len(requests)

            return requests, total_count
        except PostgrestAPIError as e:
            logger.error(f"Database error getting generation requests: {e.message}")
            raise RepositoryError(
                f"Failed to get generation requests: {e.message}"
            ) from e

    async def delete_request(self, request_id: UUID) -> bool:
        """
        Delete a generation request by ID.

        Note: This does NOT delete associated problems. Problems retain their
        generation_request_id as a historical reference.

        Args:
            request_id: ID of the generation request to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            result = (
                await self.client.table("generation_requests")
                .delete()
                .eq("id", str(request_id))
                .execute()
            )
            return len(result.data) > 0 if result.data else False
        except PostgrestAPIError as e:
            logger.error(f"Database error deleting generation request: {e.message}")
            raise RepositoryError(
                f"Failed to delete generation request: {e.message}"
            ) from e

    async def delete_old_requests(
        self,
        older_than: timedelta | None = None,
        statuses: list[GenerationStatus] | None = None,
        metadata_contains: dict[str, Any] | None = None,
    ) -> int:
        """
        Delete generation requests, optionally filtered by age, status, and metadata.

        Args:
            older_than: Optional duration - delete requests older than this (timedelta).
                       If None, age filtering is skipped (matches all ages).
            statuses: Optional list of statuses to filter (defaults to completed/failed/expired)
            metadata_contains: Optional dict to filter by metadata JSONB containment.
                              Example: {"topic_tags": ["test_data"]} to match requests
                              with "test_data" in metadata.topic_tags array.

        Returns:
            Number of requests deleted
        """
        if statuses is None:
            statuses = [
                GenerationStatus.COMPLETED,
                GenerationStatus.FAILED,
                GenerationStatus.EXPIRED,
            ]

        try:
            query = self.client.table("generation_requests").delete()

            # Filter by age if provided
            if older_than is not None:
                cutoff = datetime.now(UTC) - older_than
                query = query.lt("requested_at", cutoff.isoformat())

            # Filter by statuses
            status_values = [s.value for s in statuses]
            query = query.in_("status", status_values)

            # Filter by metadata if provided
            if metadata_contains:
                query = query.contains("metadata", metadata_contains)

            result = await query.execute()
            return len(result.data) if result.data else 0
        except PostgrestAPIError as e:
            logger.error(f"Database error deleting old requests: {e.message}")
            raise RepositoryError(f"Failed to delete old requests: {e.message}") from e

    async def expire_stale_pending_requests(
        self,
        older_than_minutes: int = 10,
        skip_test_data: bool = True,
    ) -> int:
        """
        Mark old PENDING requests as EXPIRED.

        Requests that have been in PENDING state for too long likely never
        got picked up from Kafka (service crash, rebalance, etc.).

        Args:
            older_than_minutes: Mark PENDING requests older than this as EXPIRED
            skip_test_data: If True, skip requests with "test_data" in metadata.topic_tags.
                           This prevents test data from being expired during parallel test runs.

        Returns:
            Number of requests marked as expired
        """
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(minutes=older_than_minutes)

        try:
            query = (
                self.client.table("generation_requests")
                .update(
                    {
                        "status": GenerationStatus.EXPIRED.value,
                        "completed_at": datetime.now(UTC).isoformat(),
                        "error_message": f"Expired after {older_than_minutes} minutes in pending state",
                    }
                )
                .eq("status", GenerationStatus.PENDING.value)
                .lt("requested_at", cutoff.isoformat())
            )

            # Skip test data to avoid expiring requests created by parallel tests
            if skip_test_data:
                # Use NOT contains to exclude test data
                # PostgREST: .not_.contains() excludes rows where metadata contains the filter
                query = query.not_.contains("metadata", {"topic_tags": ["test_data"]})

            result = await query.execute()
            expired_count = len(result.data) if result.data else 0

            if expired_count > 0:
                logger.info(
                    f"Marked {expired_count} stale PENDING requests as EXPIRED "
                    f"(older than {older_than_minutes} minutes)"
                )

            return expired_count
        except PostgrestAPIError as e:
            logger.error(f"Database error expiring stale requests: {e.message}")
            raise RepositoryError(
                f"Failed to expire stale requests: {e.message}"
            ) from e
