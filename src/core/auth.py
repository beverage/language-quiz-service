"""
Authentication middleware for API key validation.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.clients.supabase import get_supabase_client
from src.schemas.api_keys import verify_api_key, check_ip_allowed
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication and authorization."""

    def __init__(self, app, exempt_paths: List[str] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or []

    async def dispatch(self, request: Request, call_next):
        """Process the request and validate API key if required."""

        # Check if this path is exempt from authentication
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        try:
            # Extract API key from headers
            api_key = self._extract_api_key(request)
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required. Provide X-API-Key header.",
                )

            # Validate API key and get key info
            key_info = await self._validate_api_key(api_key)
            if not key_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
                )

            # Check if key is active
            if not key_info.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key is inactive",
                )

            # Check IP allowlist if configured
            client_ip = self._get_client_ip(request)
            allowed_ips = key_info.get("allowed_ips")
            if not check_ip_allowed(client_ip, allowed_ips):
                logger.warning(
                    f"IP {client_ip} not allowed for API key {key_info.get('key_prefix')}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access denied: IP not in allowlist",
                )

            # Update usage tracking
            await self._update_key_usage(key_info["id"])

            # Add key info to request state for downstream use
            request.state.api_key_info = key_info
            request.state.client_ip = client_ip

            # Continue processing the request
            response = await call_next(request)
            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error",
            )

    def _is_exempt_path(self, path: str) -> bool:
        """Check if the request path is exempt from authentication."""
        try:
            settings = get_settings()

            # Always exempt health and metrics
            exempt_patterns = ["/health", "/metrics"]

            # Exempt root path exactly
            if path == "/":
                return True

            # In non-production, also exempt docs
            if not settings.is_production:
                exempt_patterns.extend(["/docs", "/redoc", "/openapi.json"])

            # Add any additional exempt paths
            exempt_patterns.extend(self.exempt_paths)

            return any(path.startswith(pattern) for pattern in exempt_patterns)
        except Exception:
            # Fallback - only exempt health endpoints if settings fail
            return path.startswith(("/health", "/metrics", "/"))

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from X-API-Key header."""
        return request.headers.get("X-API-Key")

    def _get_client_ip(self, request: Request) -> str:
        """Extract the client IP address from the request."""
        # Check for forwarded headers first (from proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

    async def _validate_api_key(self, api_key: str) -> Optional[dict]:
        """Validate API key against database and return key info if valid."""
        try:
            client = await get_supabase_client()

            # Get all active keys to check against
            result = (
                await client.table("api_keys")
                .select("*")
                .eq("is_active", True)
                .execute()
            )

            if not result.data:
                return None

            # Check each key hash
            for key_data in result.data:
                if verify_api_key(api_key, key_data["key_hash"]):
                    return key_data

            return None

        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None

    async def _update_key_usage(self, key_id: str) -> None:
        """Update the last_used_at timestamp and increment usage_count."""
        try:
            client = await get_supabase_client()

            # Use SQL to atomically increment usage_count and update timestamp
            # This avoids race conditions and extra queries
            result = await client.rpc(
                "increment_api_key_usage", {"key_id": key_id}
            ).execute()

            # Fallback if RPC doesn't exist - will add this to SQL later
            if not result.data:
                await (
                    client.table("api_keys")
                    .update({"last_used_at": datetime.now(datetime.UTC).isoformat()})
                    .eq("id", key_id)
                    .execute()
                )

        except Exception as e:
            # Don't fail the request if usage tracking fails
            logger.warning(f"Failed to update key usage for {key_id}: {e}")


async def get_current_api_key(request: Request) -> dict:
    """Dependency to get the current API key info from request state."""
    if not hasattr(request.state, "api_key_info"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No valid API key found"
        )
    return request.state.api_key_info


def require_permission(permission: str):
    """Decorator factory to require specific permissions."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs (depends on FastAPI route signature)
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request or not hasattr(request.state, "api_key_info"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            key_info = request.state.api_key_info
            permissions = key_info.get("permissions_scope", [])

            if permission not in permissions and "admin" not in permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
