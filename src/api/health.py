"""Health check endpoints."""

from fastapi import APIRouter, Depends
from ..core.config import get_settings, Settings

router = APIRouter(tags=["health"])


@router.get("/")
async def root(settings: Settings = Depends(get_settings)):
    """Root endpoint."""
    return {
        "message": "Language Quiz Service is running",
        "service": settings.api_title,
        "version": settings.api_version,
    }


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "language-quiz-service",
        "version": settings.api_version,
        "environment": settings.environment,
    }
