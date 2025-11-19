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
        self.MAX_POLL_INTERVAL_MS: int = 900000  # 15 minutes - max time between polls
        self.SESSION_TIMEOUT_MS: int = 30000  # 30 seconds - max time without heartbeat

        # Worker behavior
        self.WORKER_COUNT: int = int(os.getenv("WORKER_COUNT", "0"))
        self.WORKER_POLL_TIMEOUT_SECONDS: float = 1.0  # How long to wait for messages

        # Validate worker count
        if self.WORKER_COUNT < 0:
            raise ValueError("WORKER_COUNT must be >= 0")
        if self.WORKER_COUNT > 10:
            import logging

            logging.warning(
                f"WORKER_COUNT={self.WORKER_COUNT} exceeds partition count (10). "
                f"Extra workers will be idle. Consider increasing topic partitions."
            )

        # Retry settings
        self.MAX_RETRY_ATTEMPTS: int = 3
        self.RETRY_BACKOFF_SECONDS: float = 2.0


# Global config instance
worker_config = WorkerConfig()
