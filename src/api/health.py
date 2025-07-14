"""Health check endpoints."""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..core.config import get_settings, Settings

router = APIRouter(tags=["health"])

# Get limiter instance
limiter = Limiter(key_func=get_remote_address)


@router.get("/")
@limiter.limit("100/minute")
async def root(request: Request, settings: Settings = Depends(get_settings)):
    """Root endpoint."""
    return {
        "message": "Language Quiz Service is running",
        "service": settings.api_title,
        "version": settings.api_version,
    }


@router.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request, settings: Settings = Depends(get_settings)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "language-quiz-service",
        "version": settings.api_version,
        "environment": settings.environment,
        "rate_limit": f"{settings.rate_limit_requests}/minute",
    }
