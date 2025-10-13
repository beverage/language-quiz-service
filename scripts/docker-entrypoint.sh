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

# Start the application
cd /app && exec /app/.venv/bin/uvicorn src.main:app --host "${WEB_HOST:-0.0.0.0}" --port "${WEB_PORT:-8000}"
