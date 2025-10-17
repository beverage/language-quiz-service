"""
Authentication middleware for API key validation.
"""

import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import get_settings
from src.services.api_key_service import ApiKeyService

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication and authorization."""

    def __init__(self, app, exempt_paths: list[str] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or []

    async def dispatch(self, request: Request, call_next):
        """Process the request and validate API key if required."""
        with tracer.start_as_current_span(
            "auth_middleware",
            attributes={
                "http.method": request.method,
                "http.route": request.url.path,
            },
        ):
            # Check if this path is exempt from authentication
            if self._is_exempt_path(request.url.path):
                return await call_next(request)

            try:
                # Extract API key from headers
                with tracer.start_as_current_span("extract_api_key"):
                    api_key = self._extract_api_key(request)
                    if not api_key:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key required. Provide X-API-Key header.",
                        )

                # Validate API key and get key info (includes IP checking and usage tracking)
                with tracer.start_as_current_span("validate_api_key"):
                    client_ip = self._get_client_ip(request)
                    key_info = await self._validate_api_key_with_ip(api_key, client_ip)
                    if not key_info:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid API key",
                        )

                # Add key info to request state for downstream use
                request.state.api_key_info = key_info
                request.state.client_ip = client_ip

                # Continue processing the request
                response = await call_next(request)
                return response

            except HTTPException as exc:
                # Return standardized JSON response for authentication errors
                return JSONResponse(
                    status_code=exc.status_code,
                    content={
                        "error": True,
                        "message": exc.detail,
                        "status_code": exc.status_code,
                        "path": str(request.url.path),
                    },
                )
            except Exception as e:
                logger.error(f"Authentication middleware error: {e}", exc_info=True)
                # Return standardized JSON response for unexpected auth errors
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": True,
                        "message": "Authentication service error",
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "path": str(request.url.path),
                    },
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

    def _extract_api_key(self, request: Request) -> str | None:
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

    async def _validate_api_key_with_ip(
        self, api_key: str, client_ip: str
    ) -> dict | None:
        """Validate API key against database with IP checking and return key info if valid."""
        try:
            # Use the ApiKeyService for validation (handles IP checking and usage tracking)
            service = ApiKeyService()
            result = await service.authenticate_api_key(api_key, client_ip)

            if result:
                return result.model_dump()

            return None

        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None


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
