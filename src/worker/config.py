"""Worker configuration."""

import os


class WorkerConfig:
    """Configuration for the background worker."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Kafka connection
        self.KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )

        # Topic names
        self.PROBLEM_GENERATION_TOPIC: str = "problem-generation-requests"

        # Consumer settings
        self.CONSUMER_GROUP_ID: str = "problem-generator-workers"
        self.CONSUMER_AUTO_OFFSET_RESET: str = (
            "earliest"  # Start from beginning if no offset
        )

        # Processing settings
        self.MAX_POLL_INTERVAL_MS: int = 300000  # 5 minutes - max time between polls
        self.SESSION_TIMEOUT_MS: int = 30000  # 30 seconds - max time without heartbeat

        # Worker behavior
        self.ENABLE_WORKER: bool = os.getenv("ENABLE_WORKER", "false").lower() == "true"
        self.WORKER_POLL_TIMEOUT_SECONDS: float = 1.0  # How long to wait for messages

        # Retry settings
        self.MAX_RETRY_ATTEMPTS: int = 3
        self.RETRY_BACKOFF_SECONDS: float = 2.0


# Global config instance
worker_config = WorkerConfig()
