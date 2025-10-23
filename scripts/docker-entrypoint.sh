#!/bin/bash
# Entrypoint for Language Quiz Service container
# Starts uvicorn server with configurable host and port
# OpenTelemetry is configured in src/main.py based on environment variables

set -e

# Ensure virtualenv is in PATH
export PATH="/app/.venv/bin:$PATH"

echo "🚀 Starting Language Quiz Service..."
echo "   Environment: ${ENVIRONMENT:-development}"
echo "   Host: ${WEB_HOST:-0.0.0.0}"
echo "   Port: ${WEB_PORT:-8000}"

if [ -n "$OTEL_EXPORTER_OTLP_ENDPOINT" ]; then
    echo "📊 OpenTelemetry enabled - sending to: $OTEL_EXPORTER_OTLP_ENDPOINT"
else
    echo "⚡ OpenTelemetry disabled (no OTEL_EXPORTER_OTLP_ENDPOINT set)"
fi

# Build uvicorn command with optional reload flag for local development
UVICORN_CMD="/app/.venv/bin/uvicorn src.main:app --host ${WEB_HOST:-0.0.0.0} --port ${WEB_PORT:-8000}"

if [ "${ENVIRONMENT}" = "local" ] || [ "${ENVIRONMENT}" = "development" ]; then
    echo "🔄 Hot-reload enabled"
    UVICORN_CMD="$UVICORN_CMD --reload"
fi

# Start the application
cd /app && exec $UVICORN_CMD
