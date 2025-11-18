"""Generation requests repository for data access."""

import logging
from uuid import UUID

from postgrest import APIError as PostgrestAPIError

from src.clients.supabase import get_supabase_client
from src.core.exceptions import RepositoryError
from src.schemas.generation_requests import (
    GenerationRequest,
    GenerationRequestCreate,
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
