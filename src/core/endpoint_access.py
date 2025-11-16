"""Endpoint access control middleware for production/staging."""

import logging
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings

logger = logging.getLogger(__name__)

# Endpoints that are publicly accessible in production/staging
PUBLIC_ENDPOINTS = [
    "/api/v1/problems/random",  # GET - Retrieve random problem from database
    "/api/v1/problems/generate",  # POST - Generate new problem with AI
    "/health",  # GET - Health check (for monitoring)
    "/",  # GET - Root endpoint
    "/docs",  # GET - API docs (optional, can remove in production)
    "/openapi.json",  # GET - OpenAPI spec
]


class EndpointAccessMiddleware(BaseHTTPMiddleware):
    """
    Middleware to restrict endpoint access in production/staging environments.

    Only allows access to PUBLIC_ENDPOINTS when running in staging/production.
    In development, all endpoints are accessible.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()

        # In development, allow all endpoints
        if settings.is_development:
            return await call_next(request)

        # In staging/production, restrict to public endpoints
        path = request.url.path
        method = request.method

        # Check if this is a public endpoint
        is_public = any(
            path.startswith(endpoint) or path == endpoint
            for endpoint in PUBLIC_ENDPOINTS
        )

        if not is_public:
            logger.warning(
                f"Blocked access to restricted endpoint: {method} {path} "
                f"from {request.client.host if request.client else 'unknown'} "
                f"(environment: {settings.environment})"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "message": "This endpoint is not publicly accessible",
                    "detail": "Access to this endpoint is restricted in production/staging environments",
                },
            )

        # Endpoint is public, proceed
        return await call_next(request)
