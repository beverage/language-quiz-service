"""API Key repository for data access."""

import logging
from uuid import UUID

from src.core.exceptions import RepositoryError
from src.schemas.api_keys import ApiKey, ApiKeyCreate, ApiKeyStats, ApiKeyUpdate
from supabase import AsyncClient

logger = logging.getLogger(__name__)


class ApiKeyRepository:
    """Repository for API key data access operations."""

    def __init__(self, client: AsyncClient):
        """Initialize the repository with a Supabase async client."""
        self.client = client

    async def create_api_key(
        self, api_key: ApiKeyCreate, key_hash: str, key_prefix: str
    ) -> ApiKey:
        """Create a new API key."""
        api_key_dict = api_key.model_dump()

        # Convert UUID to string if needed
        for key, value in api_key_dict.items():
            if isinstance(value, UUID):
                api_key_dict[key] = str(value)

        # Add the computed fields
        api_key_dict.update(
            {
                "key_hash": key_hash,
                "key_prefix": key_prefix,
            }
        )

        result = await self.client.table("api_keys").insert(api_key_dict).execute()

        if result.data:
            return ApiKey.model_validate(result.data[0])
        raise RepositoryError("Failed to create API key: No data returned.")

    async def get_api_key(self, api_key_id: UUID) -> ApiKey | None:
        """Get an API key by ID."""
        result = (
            await self.client.table("api_keys")
            .select("*")
            .eq("id", str(api_key_id))
            .execute()
        )

        if result.data:
            return ApiKey.model_validate(result.data[0])
        return None

    async def get_api_key_by_hash(self, key_hash: str) -> ApiKey | None:
        """Get an API key by its hash (for authentication)."""
        result = (
            await self.client.table("api_keys")
            .select("*")
            .eq("key_hash", key_hash)
            .eq("is_active", True)
            .execute()
        )

        if result.data:
            return ApiKey.model_validate(result.data[0])
        return None

    async def get_api_key_by_prefix(self, key_prefix: str) -> ApiKey | None:
        """Get an API key by its prefix (for authentication)."""
        result = (
            await self.client.table("api_keys")
            .select("*")
            .eq("key_prefix", key_prefix)
            .eq("is_active", True)
            .execute()
        )

        if result.data:
            return ApiKey.model_validate(result.data[0])
        return None

    async def get_all_api_keys(
        self, limit: int = 100, include_inactive: bool = False
    ) -> list[ApiKey]:
        """Get all API keys with optional filtering."""
        query = self.client.table("api_keys").select("*").limit(limit)

        if not include_inactive:
            query = query.eq("is_active", True)

        query = query.order("created_at", desc=True)

        result = await query.execute()
        return [ApiKey.model_validate(key) for key in result.data]

    async def update_api_key(
        self, api_key_id: UUID, api_key_data: ApiKeyUpdate
    ) -> ApiKey | None:
        """Update an API key."""
        update_dict = api_key_data.model_dump(exclude_unset=True)

        if not update_dict:
            # No fields to update, return current key
            return await self.get_api_key(api_key_id)

        result = (
            await self.client.table("api_keys")
            .update(update_dict)
            .eq("id", str(api_key_id))
            .execute()
        )

        if result.data:
            return ApiKey.model_validate(result.data[0])
        return None

    async def delete_api_key(self, api_key_id: UUID) -> bool:
        """Delete an API key (soft delete by setting is_active=False)."""
        result = (
            await self.client.table("api_keys")
            .update({"is_active": False})
            .eq("id", str(api_key_id))
            .execute()
        )
        return len(result.data) > 0

    async def increment_usage(self, api_key_id: UUID) -> bool:
        """Increment the usage count and update last_used_at atomically."""
        try:
            # Use the atomic database function
            await self.client.rpc(
                "increment_api_key_usage", {"key_id": str(api_key_id)}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to increment usage for API key {api_key_id}: {e}")
            return False

    async def get_api_key_stats(self) -> ApiKeyStats:
        """Get API key usage statistics."""
        # Get counts
        all_keys_result = (
            await self.client.table("api_keys")
            .select("id, is_active, usage_count")
            .execute()
        )

        if not all_keys_result.data:
            return ApiKeyStats(
                total_keys=0, active_keys=0, inactive_keys=0, total_requests=0
            )

        total_keys = len(all_keys_result.data)
        active_keys = sum(1 for key in all_keys_result.data if key["is_active"])
        inactive_keys = total_keys - active_keys
        total_requests = sum(key["usage_count"] or 0 for key in all_keys_result.data)

        # Get most active key
        most_active_key = None
        if all_keys_result.data:
            max_usage_key = max(
                all_keys_result.data, key=lambda k: k["usage_count"] or 0
            )
            if max_usage_key["usage_count"] and max_usage_key["usage_count"] > 0:
                # Get the key_prefix for the most active key
                key_result = (
                    await self.client.table("api_keys")
                    .select("key_prefix")
                    .eq("id", max_usage_key["id"])
                    .execute()
                )
                if key_result.data:
                    most_active_key = key_result.data[0]["key_prefix"]

        # Get requests in last 24 hours (simplified - would need more complex query in real app)
        requests_last_24h = None  # Would require timestamp analysis

        return ApiKeyStats(
            total_keys=total_keys,
            active_keys=active_keys,
            inactive_keys=inactive_keys,
            total_requests=total_requests,
            requests_last_24h=requests_last_24h,
            most_active_key=most_active_key,
        )

    async def find_keys_by_name(self, name_pattern: str) -> list[ApiKey]:
        """Find API keys by name pattern (case-insensitive)."""
        result = (
            await self.client.table("api_keys")
            .select("*")
            .ilike("name", f"%{name_pattern}%")
            .order("created_at", desc=True)
            .execute()
        )

        return [ApiKey.model_validate(key) for key in result.data]

    async def count_active_keys(self) -> int:
        """Count active API keys."""
        result = (
            await self.client.table("api_keys")
            .select("id", count="exact")
            .eq("is_active", True)
            .execute()
        )

        return result.count or 0
