"""
Smoke tests for basic service functionality.

Quick sanity checks that the service is running and responding correctly.
"""

import pytest


@pytest.mark.acceptance
@pytest.mark.smoke
def test_health_endpoint(http_client, service_url):
    """Health endpoint should return 200 OK."""
    response = http_client.get(f"{service_url}/health")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert data.get("status") == "healthy"


@pytest.mark.acceptance
@pytest.mark.smoke
def test_root_endpoint(http_client, service_url):
    """Root endpoint should return service information."""
    response = http_client.get(f"{service_url}/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    # Should have basic service info
    for key in ("message", "service", "version"):
        assert key in data, f"Missing key '{key}' in root response"


@pytest.mark.acceptance
@pytest.mark.smoke
def test_get_random_verb(http_client, service_url, auth_headers):
    """Test basic verb retrieval functionality."""
    response = http_client.get(
        f"{service_url}/api/v1/verbs/random", headers=auth_headers
    )
    assert (
        response.status_code == 200
    ), f"Failed to get random verb: {response.status_code} - {response.text}"

    verb = response.json()

    # Verify verb structure
    assert "infinitive" in verb
    assert "target_language_code" in verb
    assert "auxiliary" in verb
    assert "reflexive" in verb

    # Verify data types
    assert isinstance(verb["infinitive"], str)
    assert isinstance(verb["target_language_code"], str)
    assert isinstance(verb["reflexive"], bool)


@pytest.mark.acceptance
@pytest.mark.smoke
def test_verb_endpoint_exists(http_client, service_url, auth_headers):
    """Test that verb random endpoint is accessible."""
    # Note: This API doesn't have a list endpoint, only /random
    response = http_client.get(
        f"{service_url}/api/v1/verbs/random", headers=auth_headers
    )
    assert response.status_code == 200


@pytest.mark.acceptance
@pytest.mark.smoke
def test_cache_stats_accessible(http_client, service_url, auth_headers):
    """Cache stats endpoint should be accessible with valid auth."""
    response = http_client.get(
        f"{service_url}/api/v1/cache/stats", headers=auth_headers
    )
    assert response.status_code == 200

    stats = response.json()

    # Verify cache stats structure
    assert "verb_cache" in stats
    assert "conjugation_cache" in stats
    assert "api_key_cache" in stats

    # Each cache should have expected fields
    for cache_name in ["verb_cache", "conjugation_cache", "api_key_cache"]:
        cache = stats[cache_name]
        assert "loaded" in cache
        assert isinstance(cache["loaded"], bool)


@pytest.mark.acceptance
@pytest.mark.smoke
def test_service_handles_invalid_endpoints(http_client, service_url, auth_headers):
    """Service should return 404 for non-existent endpoints."""
    response = http_client.get(
        f"{service_url}/api/v1/nonexistent", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.acceptance
@pytest.mark.smoke
def test_service_handles_invalid_methods(http_client, service_url, auth_headers):
    """Service should reject invalid HTTP methods."""
    # Try DELETE on a GET-only endpoint
    response = http_client.delete(
        f"{service_url}/api/v1/verbs/random", headers=auth_headers
    )
    assert response.status_code in [405, 404]  # Method Not Allowed or Not Found
