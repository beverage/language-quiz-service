FROM redis:7.2-alpine

# Install redis_exporter for Prometheus metrics
RUN apk add --no-cache wget ca-certificates && \
    wget -O /tmp/redis_exporter.tar.gz https://github.com/oliver006/redis_exporter/releases/download/v1.55.0/redis_exporter-v1.55.0.linux-amd64.tar.gz && \
    tar -xzf /tmp/redis_exporter.tar.gz -C /tmp && \
    mv /tmp/redis_exporter-v1.55.0.linux-amd64/redis_exporter /usr/local/bin/ && \
    chmod +x /usr/local/bin/redis_exporter && \
    rm -rf /tmp/redis_exporter* && \
    apk del wget

# Copy custom Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf
COPY start-redis.sh /start-redis.sh

# Make startup script executable
RUN chmod +x /start-redis.sh

# Expose Redis port and metrics port
EXPOSE 6379 9091

# Use custom startup script to handle environment variables
CMD ["/start-redis.sh"]
