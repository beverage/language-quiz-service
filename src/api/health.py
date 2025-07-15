"""Health check endpoints."""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..core.config import get_settings, Settings

router = APIRouter(tags=["health"])

# Get limiter instance
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/",
    summary="API service root endpoint",
    description="""
    Root endpoint providing basic service information.
    
    **Use Cases**:
    - Verify API is running and accessible
    - Check service version and basic configuration
    - First endpoint to test when setting up API access
    
    **Rate Limit**: 100 requests per minute
    **Authentication**: Not required
    """,
    responses={
        200: {
            "description": "Service information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Language Quiz Service is running",
                        "service": "Language Quiz Service API",
                        "version": "1.0.0",
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Rate limit exceeded",
                        "status_code": 429,
                        "path": "/",
                    }
                }
            },
        },
    },
)
@limiter.limit("100/minute")
async def root(request: Request, settings: Settings = Depends(get_settings)):
    """Root endpoint."""
    return {
        "message": "Language Quiz Service is running",
        "service": settings.api_title,
        "version": settings.api_version,
    }


@router.get(
    "/health",
    summary="Comprehensive health check",
    description="""
    Comprehensive health check endpoint with detailed system information.
    
    **Returns**:
    - Service status and version
    - Environment information (production/staging/development)
    - Rate limiting configuration
    - System health indicators
    
    **Use Cases**:
    - Monitor service availability
    - Check environment configuration
    - Verify rate limiting settings
    - Integration with monitoring systems
    
    **Rate Limit**: 100 requests per minute
    **Authentication**: Not required
    """,
    responses={
        200: {
            "description": "Health check completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "language-quiz-service",
                        "version": "1.0.0",
                        "environment": "production",
                        "rate_limit": "100/minute",
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Rate limit exceeded",
                        "status_code": 429,
                        "path": "/health",
                    }
                }
            },
        },
    },
)
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
