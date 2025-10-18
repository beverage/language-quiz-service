"""
Shared fixtures for acceptance tests.

Acceptance tests run against a real deployed service (staging/production in CI,
or local :7900 service in development).
"""

import os
from collections.abc import Generator

import httpx
import pytest


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
def service_api_key() -> str:
    """
    Get API key from environment.

    Required for testing authenticated endpoints.
    """
    api_key = os.getenv("SERVICE_API_KEY")
    if not api_key:
        pytest.fail(
            "SERVICE_API_KEY environment variable required for acceptance tests"
        )
    return api_key


@pytest.fixture(scope="session")
def auth_headers(service_api_key: str) -> dict[str, str]:
    """HTTP headers with API key authentication."""
    return {
        "X-API-Key": service_api_key,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def http_client() -> Generator[httpx.Client, None, None]:
    """Session-scoped HTTP client for acceptance tests."""
    with httpx.Client(timeout=30.0) as client:
        yield client
