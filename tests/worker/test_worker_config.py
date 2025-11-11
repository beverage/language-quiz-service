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
        assert config.ENABLE_WORKER is False
        assert config.MAX_RETRY_ATTEMPTS == 3

    def test_config_from_environment_variables(self):
        """Test worker configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "KAFKA_BOOTSTRAP_SERVERS": "kafka-prod:9092",
                "ENABLE_WORKER": "true",
            },
            clear=True,
        ):
            config = WorkerConfig()

            assert config.KAFKA_BOOTSTRAP_SERVERS == "kafka-prod:9092"
            assert config.ENABLE_WORKER is True

    def test_enable_worker_flag_parsing(self):
        """Test ENABLE_WORKER flag parsing handles various inputs."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("", False),
            ("invalid", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"ENABLE_WORKER": env_value}, clear=True):
                config = WorkerConfig()
                assert (
                    config.ENABLE_WORKER == expected
                ), f"ENABLE_WORKER='{env_value}' should parse to {expected}"
