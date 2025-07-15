"""
Language Quiz Service FastAPI Application

This module sets up the FastAPI application with all necessary configurations,
middleware, and route handlers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import health
from .api import api_keys
from .api import verbs
from .core.config import get_settings
from .core.auth import ApiKeyAuthMiddleware

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

    ### 🔐 Authentication

    All API endpoints require authentication using API keys. Include your API key in the 
    `Authorization` header as a Bearer token:

    ```
    Authorization: Bearer sk_live_your_api_key_here
    ```

    ### 📋 Permission Levels

    - **read**: Access to GET endpoints for retrieving data
    - **write**: Access to POST endpoints for creating and downloading content
    - **admin**: Full access including API key management

    ### 🚀 Getting Started

    1. **Obtain an API Key**: Contact your administrator to get an API key
    2. **Test Authentication**: Use the `/health` endpoint to verify your setup
    3. **Explore Verbs**: Start with `/verbs/random` to get a random French verb
    4. **Download Content**: Use `/verbs/download` to add new verbs to the database

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
            "url": "https://api.languagequizservice.com",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.languagequizservice.com",
            "description": "Staging server",
        },
        {"url": "http://localhost:8000", "description": "Local development server"},
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
app.include_router(api_keys.router)
app.include_router(verbs.router)


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with detailed error responses."""
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
