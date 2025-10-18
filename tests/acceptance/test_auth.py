"""
Authentication acceptance tests.

Validates that the service properly enforces authentication and authorization.
"""

import pytest


@pytest.mark.acceptance
@pytest.mark.auth
def test_public_endpoints_work_without_auth(http_client, service_url):
    """Public endpoints should be accessible without authentication."""
    # Health endpoint should always be public
    response = http_client.get(f"{service_url}/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.acceptance
@pytest.mark.auth
def test_protected_endpoints_reject_no_auth(http_client, service_url):
    """API endpoints should reject requests without API keys."""
    protected_endpoints = [
        "/api/v1/verbs",
        "/api/v1/verbs/random",
        "/api/v1/sentences",
        "/api/v1/problems",
        "/api/v1/api-keys",
        "/api/v1/cache/stats",
    ]

    for endpoint in protected_endpoints:
        response = http_client.get(f"{service_url}{endpoint}")
        assert response.status_code in [
            401,
            403,
        ], f"{endpoint} returned {response.status_code}, expected 401 or 403"


@pytest.mark.acceptance
@pytest.mark.auth
def test_protected_endpoints_reject_invalid_key(http_client, service_url):
    """API endpoints should reject requests with invalid API keys."""
    invalid_headers = {"X-API-Key": "invalid_key_12345"}

    protected_endpoints = [
        "/api/v1/verbs/random",
        "/api/v1/cache/stats",
    ]

    for endpoint in protected_endpoints:
        response = http_client.get(f"{service_url}{endpoint}", headers=invalid_headers)
        assert response.status_code in [
            401,
            403,
        ], f"{endpoint} accepted invalid key (returned {response.status_code})"


@pytest.mark.acceptance
@pytest.mark.auth
def test_protected_endpoints_accept_valid_key(http_client, service_url, auth_headers):
    """API endpoints should work with valid API keys."""
    # Test read endpoint
    response = http_client.get(
        f"{service_url}/api/v1/verbs/random", headers=auth_headers
    )
    assert (
        response.status_code == 200
    ), f"Valid API key rejected: {response.status_code} - {response.text}"

    # Verify response structure
    data = response.json()
    assert "infinitive" in data, f"Missing 'infinitive' in response: {data}"
    assert (
        "target_language_code" in data
    ), f"Missing 'target_language_code' in response: {data}"


@pytest.mark.acceptance
@pytest.mark.auth
def test_require_auth_cannot_be_bypassed(http_client, service_url):
    """
    Verify REQUIRE_AUTH enforcement cannot be bypassed.

    This is the critical security test - if REQUIRE_AUTH=false was accidentally
    deployed, this test will catch it.
    """
    # Try various bypass attempts
    bypass_attempts = [
        # Try to spoof localhost
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Real-IP": "127.0.0.1"},
        # Try to bypass with various headers
        {"X-Development-Mode": "true"},
        {"X-Auth-Bypass": "true"},
        # Empty API key
        {"X-API-Key": ""},
    ]

    endpoint = f"{service_url}/api/v1/verbs/random"

    for headers in bypass_attempts:
        response = http_client.get(endpoint, headers=headers)
        assert response.status_code in [
            401,
            403,
        ], f"Auth bypass successful with headers {headers}: {response.status_code}"


@pytest.mark.acceptance
@pytest.mark.auth
def test_cache_stats_requires_auth(http_client, service_url, auth_headers):
    """Cache stats endpoint should require authentication."""
    # Without auth
    response = http_client.get(f"{service_url}/api/v1/cache/stats")
    assert response.status_code in [401, 403]

    # With auth
    response = http_client.get(
        f"{service_url}/api/v1/cache/stats", headers=auth_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert "verb_cache" in data
    assert "conjugation_cache" in data
    assert "api_key_cache" in data
