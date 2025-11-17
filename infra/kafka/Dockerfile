FROM apache/kafka:3.8.0

# Kafka runs as user 'appuser' (uid 1000)
# The official image already sets up everything we need

# Install network debugging tools and create data directory
# Note: On Fly.io, /var/lib/kafka/data will be the volume mount point (contains lost+found)
# We create a subdirectory for Kafka logs to avoid Kafka scanning lost+found
USER root
RUN apt-get update && apt-get install -y \
    dnsutils \
    iputils-ping \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/lib/kafka/data/kafka-logs \
    && chown -R appuser:appuser /var/lib/kafka/data

# Copy topic migration scripts and definitions
# Note: Paths are relative to repo root when deploying via Fly.io
COPY infra/kafka/scripts/ /opt/kafka/migration-scripts/
COPY infra/kafka/topics/ /opt/kafka/topics/
RUN chmod +x /opt/kafka/migration-scripts/*.sh

USER appuser

# The official image's entrypoint handles KRaft initialization and startup
# based on environment variables we provide in fly.toml
#
# Topic migrations can be run manually after deployment:
#   flyctl ssh console -a <app-name> -C "/opt/kafka/migration-scripts/init-topics.sh localhost:9092 /opt/kafka/topics"

