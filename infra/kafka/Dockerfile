FROM apache/kafka:3.8.0

# Kafka runs as user 'appuser' (uid 1000)
# The official image already sets up everything we need

# Create data directory with correct permissions
USER root
RUN mkdir -p /var/lib/kafka/data && \
    chown -R appuser:appuser /var/lib/kafka/data

USER appuser

# The official image's entrypoint handles KRaft initialization and startup
# based on environment variables we provide in fly.toml

