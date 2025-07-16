"""
Language Quiz Service FastAPI Application

This module sets up the FastAPI application with all necessary configurations,
middleware, and route handlers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import api_keys, health, sentences, verbs
from .core.auth import ApiKeyAuthMiddleware
from .core.config import get_settings
from .core.exceptions import AppException

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Configure rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_requests}/minute"],
    storage_uri="memory://",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🚀 Starting Language Quiz Service...")
    logger.info(f"📊 Rate limiting: {settings.rate_limit_requests} requests/minute")
    logger.info(f"🌐 Environment: {settings.environment}")
    yield
    logger.info("🔄 Shutting down Language Quiz Service...")


app = FastAPI(
    title="Language Quiz Service API",
    description="""
    ## AI-Powered Language Learning Quiz Generation Service

    This API provides endpoints for managing French verbs, generating language learning content,
    and creating personalized quizzes using AI technology.

    ### 🌐 API Versioning

    - **Health endpoints**: Available at root level (`/health`, `/`)
    - **API endpoints**: Versioned under `/api/v1/` (e.g., `/api/v1/verbs`, `/api/v1/api-keys`)

    ### 🔐 Authentication

    All API endpoints require authentication using API keys. Include your API key in the
    `X-API-Key` header:

    ```
    X-API-Key: sk_live_your_api_key_here
    ```

    ### 📋 Permission Levels

    - **read**: Access to GET endpoints for retrieving data
    - **write**: Access to POST endpoints for creating and downloading content
    - **admin**: Full access including API key management

    ### 🚀 Getting Started

    1. **Obtain an API Key**: Contact your administrator to get an API key
    2. **Test Authentication**: Use the `/health` endpoint to verify your setup
    3. **Explore Verbs**: Start with `/api/v1/verbs/random` to get a random French verb
    4. **Download Content**: Use `/api/v1/verbs/download` to add new verbs to the database

    ### 📊 Rate Limiting

    All endpoints are rate-limited to prevent abuse:
    - Default: 100 requests per minute
    - Health endpoints: 100 requests per minute
    - Custom limits may apply based on your API key configuration

    ### 🛠️ Error Handling

    The API uses standard HTTP status codes:
    - `200`: Success
    - `400`: Bad Request (validation errors)
    - `401`: Unauthorized (missing or invalid API key)
    - `403`: Forbidden (insufficient permissions)
    - `404`: Not Found
    - `429`: Too Many Requests (rate limit exceeded)
    - `500`: Internal Server Error

    ### 🔄 Response Format

    All responses follow a consistent JSON format with appropriate HTTP status codes.
    Error responses include detailed error messages to help with debugging.

    ### 📚 Examples

    Check the interactive documentation below for detailed examples of each endpoint,
    including request/response schemas and example payloads.
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Language Quiz Service",
        "url": "https://github.com/your-org/language-quiz-service",
        "email": "support@languagequizservice.com",
    },
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    servers=[
        {
            "url": "https://api.languagequizservice.com/api/v1",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.languagequizservice.com/api/v1",
            "description": "Staging server",
        },
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Local development server",
        },
    ],
    openapi_tags=[
        {"name": "health", "description": "Health check and system status endpoints"},
        {
            "name": "verbs",
            "description": "French verb management and conjugation endpoints",
        },
        {
            "name": "api-keys",
            "description": "API key management endpoints (admin only)",
        },
        {
            "name": "problems",
            "description": "Quiz problem generation endpoints (coming soon)",
        },
        {
            "name": "sentences",
            "description": "Sentence generation endpoints (coming soon)",
        },
    ],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.production_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    if settings.is_production
    else ["*"],
    allow_headers=["*"],
)

# Add API key authentication middleware
app.add_middleware(ApiKeyAuthMiddleware)

# Include API routers
app.include_router(health.router)

# Create v1 API router
ROUTER_PREFIX = "/api/v1"

v1_router = APIRouter(prefix=ROUTER_PREFIX)
v1_router.include_router(api_keys.router)
v1_router.include_router(verbs.router)
v1_router.include_router(sentences.router)

# TODO: Uncomment these when endpoints are implemented
# v1_router.include_router(problems.router)

# Include the v1 router in the main app
app.include_router(v1_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with detailed error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )


# Unified exception handler for HTTP, application, and other errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle exceptions, routing them based on type."""
    # Application-specific exceptions (custom AppException and subclasses)
    if isinstance(exc, AppException):
        logger.error(f"AppException: {exc.message}", exc_info=True)
        response = {
            "error": True,
            "message": exc.message,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        }
        if exc.details is not None:
            response["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=response)

    # Unhandled exceptions -> Internal Server Error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path),
        },
    )
