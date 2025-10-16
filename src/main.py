"""
Language Quiz Service FastAPI Application

This module sets up the FastAPI application with all necessary configurations,
middleware, and route handlers.
"""

import base64
import logging
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import api_keys, health, problems, sentences, verbs
from .core.auth import ApiKeyAuthMiddleware
from .core.config import get_settings
from .core.exceptions import (
    AppException,
    ContentGenerationError,
    NotFoundError,
    ValidationError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================================================
# OpenTelemetry Setup (Conditional - only if OTEL_EXPORTER_OTLP_ENDPOINT set)
# ============================================================================
OTEL_ENABLED = bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))

if OTEL_ENABLED:
    logger.info("📊 Initializing OpenTelemetry instrumentation...")
    
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # ========================================================================
    # Build authentication from user-friendly env vars
    # ========================================================================
    # User only needs to set: GRAFANA_CLOUD_INSTANCE_ID, GRAFANA_CLOUD_API_KEY
    # We encode and set OTEL_EXPORTER_OTLP_HEADERS for the SDK
    instance_id = os.getenv("GRAFANA_CLOUD_INSTANCE_ID")
    api_key = os.getenv("GRAFANA_CLOUD_API_KEY")
    
    if instance_id and api_key:
        # Encode credentials as base64(instance_id:api_key)
        credentials = f"{instance_id}:{api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        # Set SDK env var at runtime - SDK will read this automatically
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {encoded}"
        logger.info("🔐 Using Grafana Cloud credentials for authentication")
    else:
        logger.warning("⚠️  No Grafana Cloud credentials - telemetry may fail")

    # Configure resource with service information from environment variables
    # SDK will also automatically pick up OTEL_RESOURCE_ATTRIBUTES if set
    resource_attrs = {}
    
    if service_name := os.getenv("OTEL_SERVICE_NAME"):
        resource_attrs[SERVICE_NAME] = service_name
    
    if service_namespace := os.getenv("OTEL_SERVICE_NAMESPACE"):
        resource_attrs["service.namespace"] = service_namespace
    
    if deployment_env := os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT"):
        resource_attrs["deployment.environment"] = deployment_env
    
    resource = Resource.create(attributes=resource_attrs)

    # ========================================================================
    # Set up Traces Provider
    # ========================================================================
    tracer_provider = TracerProvider(resource=resource)
    
    # SDK auto-configures from OTEL_EXPORTER_OTLP_* env vars
    otlp_trace_exporter = OTLPSpanExporter()
    
    # Add span processor
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # ========================================================================
    # Set up Metrics Provider
    # ========================================================================
    # SDK auto-configures from OTEL_EXPORTER_OTLP_* env vars
    otlp_metric_exporter = OTLPMetricExporter()
    
    # Configure periodic metric reader
    metric_reader = PeriodicExportingMetricReader(
        otlp_metric_exporter,
        export_interval_millis=15000,  # Export every 15 seconds
    )
    
    # Create meter provider
    meter_provider = MeterProvider(
        resource=resource,  # Same resource as traces
        metric_readers=[metric_reader],
    )
    
    # Set as global meter provider
    metrics.set_meter_provider(meter_provider)

    # ========================================================================
    # Instrument libraries (auto-instruments traces AND metrics)
    # ========================================================================
    AsyncPGInstrumentor().instrument()
    AioHttpClientInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    logger.info(
        f"✅ OpenTelemetry configured (traces + metrics) - sending to {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')}"
    )
else:
    logger.info("⚡ OpenTelemetry disabled (no OTEL_EXPORTER_OTLP_ENDPOINT set)")
# ============================================================================

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
            "description": "Quiz problem generation and management endpoints",
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

# Instrument FastAPI with OpenTelemetry (if enabled)
# IMPORTANT: Must be done BEFORE adding middleware
if OTEL_ENABLED:
    FastAPIInstrumentor.instrument_app(app)
    logger.info("✅ FastAPI instrumented with OpenTelemetry")

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
v1_router.include_router(problems.router)

# TODO: Uncomment these when endpoints are implemented
# v1_router.include_router(problems.router)

# Include the v1 router in the main app
app.include_router(v1_router)


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={"error": True, "message": exc.message, "status_code": 404},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle 400 Validation errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "status_code": 400,
        },
    )


@app.exception_handler(ContentGenerationError)
async def content_generation_exception_handler(
    request: Request, exc: ContentGenerationError
):
    """Handle 503 Content Generation errors."""
    return JSONResponse(
        status_code=503,
        content={"error": True, "message": exc.message, "status_code": 503},
    )


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
    # HTTP exceptions should be handled by the specific HTTP handler
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)

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
