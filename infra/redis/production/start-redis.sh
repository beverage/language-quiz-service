#!/bin/sh
# Redis startup script - PRODUCTION
# Language Quiz Service

if [ -z "$REDIS_PASSWORD" ]; then
    echo "FATAL: REDIS_PASSWORD not set"
    exit 1
fi

echo "Starting Redis for rate limiting (production)..."
echo "Starting Redis exporter for metrics on port 9091..."

# Start Redis in background
redis-server /usr/local/etc/redis/redis.conf --requirepass "$REDIS_PASSWORD" &

# Wait for Redis to start
sleep 3

# Start Redis exporter on port 9091 (for Prometheus metrics)
redis_exporter \
  --redis.addr=redis://localhost:6379 \
  --redis.password="$REDIS_PASSWORD" \
  --web.listen-address=":9091" &

echo "Redis running on port 6379"
echo "Metrics available on port 9091"

# Keep the main process alive
wait
