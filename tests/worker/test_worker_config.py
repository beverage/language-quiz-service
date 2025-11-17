"""Tests for worker configuration."""

import os
from unittest.mock import patch

import pytest

from src.worker.config import WorkerConfig


class TestWorkerConfig:
    """Test worker configuration parsing and defaults."""

    def test_default_configuration(self):
        """Test default worker configuration values."""
        config = WorkerConfig()

        assert config.KAFKA_BOOTSTRAP_SERVERS == "localhost:9092"
        assert config.PROBLEM_GENERATION_TOPIC == "problem-generation-requests"
        assert config.CONSUMER_GROUP_ID == "problem-generator-workers"
        assert config.CONSUMER_AUTO_OFFSET_RESET == "earliest"
        assert config.WORKER_COUNT == 0
        assert config.MAX_RETRY_ATTEMPTS == 3

    def test_config_from_environment_variables(self):
        """Test worker configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "KAFKA_BOOTSTRAP_SERVERS": "kafka-prod:9092",
                "WORKER_COUNT": "5",
            },
            clear=True,
        ):
            config = WorkerConfig()

            assert config.KAFKA_BOOTSTRAP_SERVERS == "kafka-prod:9092"
            assert config.WORKER_COUNT == 5

    def test_worker_count_parsing(self):
        """Test WORKER_COUNT parsing handles various inputs."""
        test_cases = [
            ("0", 0),
            ("1", 1),
            ("5", 5),
            ("10", 10),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"WORKER_COUNT": env_value}, clear=True):
                config = WorkerConfig()
                assert (
                    config.WORKER_COUNT == expected
                ), f"WORKER_COUNT='{env_value}' should parse to {expected}"

    def test_worker_count_validation(self):
        """Test WORKER_COUNT validation."""
        # Test negative value raises error
        with patch.dict(os.environ, {"WORKER_COUNT": "-1"}, clear=True):
            with pytest.raises(ValueError, match="WORKER_COUNT must be >= 0"):
                WorkerConfig()

    def test_worker_count_exceeds_partitions_warning(self, caplog):
        """Test warning when WORKER_COUNT exceeds partition count."""
        with patch.dict(os.environ, {"WORKER_COUNT": "15"}, clear=True):
            config = WorkerConfig()
            assert config.WORKER_COUNT == 15
            # Should log a warning about exceeding partition count
            assert "exceeds partition count" in caplog.text.lower()
