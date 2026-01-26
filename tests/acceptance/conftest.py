"""
Shared fixtures for acceptance tests.

Acceptance tests run against a real deployed service (staging/production in CI,
or local :7900 service in development).
"""

import asyncio
import json
import os
from collections.abc import Generator

import httpx
import pytest
from aiokafka import AIOKafkaProducer
from testcontainers.kafka import KafkaContainer

# Disable testcontainers reaper BEFORE importing testcontainers
os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"


@pytest.fixture(scope="session")
def service_url() -> str:
    """
    Get service URL based on environment.

    - If CI=true: Use SERVICE_URL from environment (staging/production)
    - If CI!=true: Use localhost:7900 (local test service)
    """
    if os.getenv("CI") == "true":
        url = os.getenv("SERVICE_URL")
        if not url:
            pytest.fail("CI=true but SERVICE_URL not set")
        return url

    # Local testing: always use :7900
    return "http://localhost:7900"


@pytest.fixture(scope="session")
def service_api_key(request) -> str:
    """
    Get API key for acceptance tests.

    - CI/Remote: Use SERVICE_API_KEY from environment (production/staging key)
    - Local: Use the dynamically generated admin key from parent conftest

    Note: test_keys fixture is defined in tests/conftest.py and is shared
    across all test types (unit, integration, acceptance).
    """
    # CI or remote testing: use real production/staging key
    if os.getenv("CI") == "true":
        api_key = os.getenv("SERVICE_API_KEY")
        if not api_key:
            pytest.fail("CI=true but SERVICE_API_KEY not set")
        return api_key

    # Local testing: use the admin key from the shared test_keys fixture
    # This key is generated once per session and stored in the local database
    # Use request.getfixturevalue() to lazy-load the fixture only when needed
    test_keys = request.getfixturevalue("test_keys")
    return test_keys["admin"]


@pytest.fixture(scope="session")
def auth_headers(service_api_key: str) -> dict[str, str]:
    """HTTP headers with API key authentication."""
    return {
        "Authorization": f"Bearer {service_api_key}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def http_client() -> Generator[httpx.Client, None, None]:
    """Session-scoped HTTP client for acceptance tests."""
    with httpx.Client(timeout=30.0) as client:
        yield client


# ==================== Kafka Infrastructure Test Fixtures ====================


@pytest.fixture(scope="session")
def kafka_container():
    """
    Session-scoped Kafka container for infrastructure acceptance tests.

    Uses testcontainers to spin up a real Kafka instance using KRaft mode.
    Binds to port 9091 (standard Kafka port - 1) to avoid conflicts.
    """
    container = (
        KafkaContainer(image="confluentinc/cp-kafka:7.5.0").with_bind_ports(
            9093, 19092
        )  # Bind internal 9093 to host 19092
    )
    container.start()

    yield container

    container.stop()


@pytest.fixture
def kafka_bootstrap_servers(kafka_container):
    """Get Kafka bootstrap servers from the test container."""
    return kafka_container.get_bootstrap_server()


@pytest.fixture
async def kafka_producer(kafka_bootstrap_servers):
    """
    Create a Kafka producer connected to the test container.

    Used to publish test messages for worker consumption in acceptance tests.
    """
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    await producer.start()

    yield producer

    await producer.stop()


@pytest.fixture
def test_message():
    """Sample test message for Kafka infrastructure testing."""
    return {
        "test": "acceptance_test",
        "data": "sample payload",
        "timestamp": "2025-11-11T00:00:00Z",
    }
