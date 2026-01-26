"""API Key service for business logic."""

import logging
from uuid import UUID

from src.cache.api_key_cache import ApiKeyCache
from src.core.exceptions import NotFoundError, RepositoryError, ServiceError
from src.repositories.api_keys_repository import ApiKeyRepository
from src.schemas.api_keys import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyStats,
    ApiKeyUpdate,
    ApiKeyWithPlainText,
    check_ip_allowed,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)

logger = logging.getLogger(__name__)


class ApiKeyService:
    """Service for API key business logic and orchestration."""

    def __init__(
        self,
        api_key_repository: ApiKeyRepository | None = None,
        api_key_cache: ApiKeyCache | None = None,
    ):
        """Initialize the API key service with injectable dependencies.

        Args:
            api_key_repository: Optional repository (can be set later for lazy init).
            api_key_cache: Optional ApiKeyCache for caching API keys.
        """
        self.api_key_repository = api_key_repository
        self.api_key_cache = api_key_cache

    def set_repository(self, api_key_repository: ApiKeyRepository) -> None:
        """Set the API key repository (for cases requiring lazy initialization)."""
        self.api_key_repository = api_key_repository

    def _get_api_key_repository(self) -> ApiKeyRepository:
        """Get the API key repository, raising if not set."""
        if self.api_key_repository is None:
            raise RuntimeError(
                "ApiKeyRepository not set. Either pass it to __init__ or call set_repository()."
            )
        return self.api_key_repository

    async def create_api_key(self, api_key_data: ApiKeyCreate) -> ApiKeyWithPlainText:
        """Create a new API key with business logic."""
        repo = self._get_api_key_repository()

        # Generate the API key and hash it
        api_key_plain, key_prefix = generate_api_key()
        key_hash = hash_api_key(api_key_plain)

        # Create the API key in the database
        api_key = await repo.create_api_key(api_key_data, key_hash, key_prefix)

        # Refresh cache with new key
        if self.api_key_cache:
            await self.api_key_cache.refresh_key(api_key)

        # Return the response with the plain text key (only time it's shown)
        return ApiKeyWithPlainText(
            api_key=api_key_plain,
            key_info=ApiKeyResponse.model_validate(api_key.model_dump()),
        )

    async def get_api_key(self, api_key_id: UUID) -> ApiKeyResponse:
        """Get an API key by ID (safe response, no sensitive data)."""
        repo = self._get_api_key_repository()
        api_key = await repo.get_api_key(api_key_id)

        if not api_key or not api_key.is_active:
            raise NotFoundError(f"API key with ID {api_key_id} not found")
        return ApiKeyResponse.model_validate(api_key.model_dump())

    async def get_all_api_keys(
        self, limit: int = 100, include_inactive: bool = False
    ) -> list[ApiKeyResponse]:
        """Get all API keys (safe response, no sensitive data)."""
        repo = self._get_api_key_repository()
        api_keys = await repo.get_all_api_keys(limit, include_inactive)

        return [ApiKeyResponse.model_validate(key.model_dump()) for key in api_keys]

    async def update_api_key(
        self, api_key_id: UUID, api_key_data: ApiKeyUpdate
    ) -> ApiKeyResponse:
        """Update an API key."""
        repo = self._get_api_key_repository()
        api_key = await repo.update_api_key(api_key_id, api_key_data)

        if not api_key:
            raise NotFoundError(f"API key with ID {api_key_id} not found")

        # Refresh cache with updated key
        if self.api_key_cache:
            await self.api_key_cache.refresh_key(api_key)

        return ApiKeyResponse.model_validate(api_key.model_dump())

    async def revoke_api_key(self, api_key_id: UUID) -> bool:
        """Revoke an API key (soft delete)."""
        repo = self._get_api_key_repository()
        success = await repo.delete_api_key(api_key_id)

        if success:
            # Invalidate cache
            if self.api_key_cache:
                await self.api_key_cache.invalidate_key(api_key_id)

        return success

    async def authenticate_api_key(
        self, api_key_plain: str, client_ip: str | None = None
    ) -> ApiKeyResponse | None:
        """
        Authenticate an API key and return key info if valid.

        Args:
            api_key_plain: The plain text API key
            client_ip: The client's IP address for IP allowlist checking

        Returns:
            ApiKeyResponse if valid, None if invalid
        """
        # Allow both production keys (sk_*) and test keys (test_key_*)
        if not api_key_plain or not (
            api_key_plain.startswith("sk_")
            or api_key_plain.startswith("test_key_")
            or api_key_plain.startswith("lqs_")
        ):
            return None

        repo = self._get_api_key_repository()

        try:
            # Get the key prefix for lookup (first 12 chars to match generation function)
            key_prefix = api_key_plain[:12]  # sk_live_ + first 4 chars

            # Try cache first (hot path optimization)
            api_key = None
            if self.api_key_cache:
                api_key = await self.api_key_cache.get_by_prefix(key_prefix)

            # Cache miss - look up in database
            if not api_key:
                api_key = await repo.get_api_key_by_prefix(key_prefix)

                # Warm cache for next time
                if api_key and api_key.is_active and self.api_key_cache:
                    await self.api_key_cache.refresh_key(api_key)

            if not api_key or not api_key.is_active:
                logger.warning(
                    f"Invalid or inactive API key used: {api_key_plain[:12]}..."
                )
                return None

            # Verify the key against the stored hash
            if not verify_api_key(api_key_plain, api_key.key_hash):
                logger.warning(f"API key verification failed: {api_key_plain[:12]}...")
                return None

            # Check IP allowlist if configured
            if client_ip and not check_ip_allowed(client_ip, api_key.allowed_ips):
                logger.warning(
                    f"IP {client_ip} not allowed for API key {api_key.name} ({api_key.key_prefix})"
                )
                return None

            # Increment usage count atomically (fire-and-forget to not block request)
            import asyncio

            asyncio.create_task(repo.increment_usage(api_key.id))

            logger.info(f"API key authenticated: {api_key.name} ({api_key.key_prefix})")

            # Return safe response
            return ApiKeyResponse.model_validate(api_key.model_dump())

        except RepositoryError as e:
            logger.error(f"Repository error during API key authentication: {e}")
            # Propagate as a service error
            raise ServiceError(
                "Failed to authenticate API key due to a data access error."
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error authenticating API key: {e}")
            # For truly unexpected errors, wrap in a generic ServiceError
            raise ServiceError(
                "An unexpected error occurred during API key authentication."
            ) from e

    async def verify_api_key_format(
        self, api_key_plain: str
    ) -> tuple[bool, str | None]:
        """
        Verify if an API key has the correct format without database lookup.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key_plain:
            return False, "API key is required"

        if not api_key_plain.startswith("sk_live_"):
            return False, "API key must start with 'sk_live_'"

        if len(api_key_plain) != 64:  # sk_live_ (8) + 56 random chars
            return False, "API key has invalid length"

        # Check if it contains only alphanumeric characters after prefix
        key_body = api_key_plain[8:]  # Remove "sk_live_" prefix
        if not key_body.isalnum():
            return False, "API key contains invalid characters"

        return True, None

    async def get_api_key_stats(self) -> ApiKeyStats:
        """Get API key usage statistics."""
        repo = self._get_api_key_repository()
        return await repo.get_api_key_stats()

    async def find_api_keys_by_name(self, name_pattern: str) -> list[ApiKeyResponse]:
        """Find API keys by name pattern."""
        repo = self._get_api_key_repository()
        api_keys = await repo.find_keys_by_name(name_pattern)

        return [ApiKeyResponse.model_validate(key.model_dump()) for key in api_keys]

    async def check_rate_limit(self, api_key: ApiKeyResponse) -> bool:
        """
        Check if an API key is within its rate limit.

        Note: This is a simplified implementation. In production, you'd want
        to use Redis or similar for proper sliding window rate limiting.
        """
        # For now, just return True - implement proper rate limiting later
        # This is where you'd check against Redis/cache for current usage
        return True

    async def is_api_key_expired(self, api_key: ApiKeyResponse) -> bool:
        """
        Check if an API key is expired.

        Note: Current schema doesn't have expiration, but this is where
        you'd add that business logic if needed.
        """
        # No expiration logic in current schema
        return False

    async def get_permissions(self, api_key: ApiKeyResponse) -> list[str]:
        """Get the permissions for an API key."""
        return api_key.permissions_scope

    async def has_permission(
        self, api_key: ApiKeyResponse, required_permission: str
    ) -> bool:
        """Check if an API key has a specific permission."""
        return (
            required_permission in api_key.permissions_scope
            or "admin" in api_key.permissions_scope
        )
