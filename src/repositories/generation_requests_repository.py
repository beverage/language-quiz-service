"""Generation requests repository for data access."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from postgrest import APIError as PostgrestAPIError

from src.clients.supabase import get_supabase_client
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

    @classmethod
    async def create(
        cls, client: AsyncClient | None = None
    ) -> "GenerationRequestRepository":
        """Asynchronously create an instance of GenerationRequestRepository."""
        if client is None:
            client = await get_supabase_client()
        return cls(client)

    def __init__(self, client: AsyncClient):
        """Initialize the repository with a Supabase client."""
        self.client = client

    async def create_generation_request(
        self, request: GenerationRequestCreate
    ) -> GenerationRequest:
        """Create a new generation request."""
        request_dict = request.model_dump(mode="json")

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
