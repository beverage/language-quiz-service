"""
Tests for the API key authentication middleware.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.auth import ApiKeyAuthMiddleware
from supabase import Client


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase Client for testing."""
    client = AsyncMock(spec=Client)
    client.execute = AsyncMock()
    client.from_ = MagicMock()  # This returns a query builder

    # Mock the query builder chain
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock()

    client.from_.return_value = query_builder
    return client


@pytest.fixture
def auth_middleware(mock_supabase_client):
    """Create auth middleware with mocked dependencies."""
    from unittest.mock import Mock

    mock_app = Mock()

    with patch("src.core.auth.get_supabase_client", return_value=mock_supabase_client):
        return ApiKeyAuthMiddleware(mock_app)


@pytest.fixture
def test_app():
    """Create test FastAPI app with auth middleware."""
    app = FastAPI()

    # Add the auth middleware
    app.add_middleware(ApiKeyAuthMiddleware)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/protected")
    async def protected():
        return {"message": "protected"}

    @app.get("/docs")
    async def docs():
        return {"docs": "swagger"}

    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.mark.unit
@pytest.mark.asyncio
class TestApiKeyAuthMiddleware:
    """Test the ApiKeyAuthMiddleware class."""

    async def test_health_endpoint_exempt(self, client):
        """Health endpoint should be accessible without API key."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    async def test_docs_endpoint_exempt_in_dev(self, client):
        """Docs endpoint should be accessible in development."""
        with patch.dict("os.environ", {"ENVIRONMENT": "development"}):
            response = client.get("/docs")
            assert response.status_code == 200

    async def test_missing_api_key(self, client):
        """Request without API key should return 401."""
        try:
            response = client.get("/protected")
            # If we get here, the request succeeded when it shouldn't have
            assert False, f"Expected 401 but got {response.status_code}"
        except Exception as e:
            # Check if it's the expected HTTPException
            if hasattr(e, "status_code") and e.status_code == 401:
                assert True  # This is expected
            else:
                # Convert the exception to a response for testing
                from fastapi.exceptions import HTTPException

                if isinstance(e, HTTPException) and e.status_code == 401:
                    assert True  # This is expected
                else:
                    raise  # Re-raise if it's not the expected exception

    async def test_invalid_api_key_format(self, client):
        """Request with invalid API key format should return 401."""
        try:
            response = client.get("/protected", headers={"X-API-Key": "invalid_key"})
            assert False, f"Expected 401 but got {response.status_code}"
        except Exception as e:
            from fastapi.exceptions import HTTPException

            if isinstance(e, HTTPException) and e.status_code == 401:
                assert True  # This is expected
            else:
                raise  # Re-raise if it's not the expected exception

    async def test_valid_api_key_success(self, client):
        """Valid API key should allow access."""

        # Mock the validation method directly to return valid key info
        async def mock_validate_api_key(self, api_key):
            return {
                "id": "test-uuid",
                "key_hash": "$2b$12$test_hash",
                "is_active": True,
                "allowed_ips": None,
            }

        # Patch the middleware's validation method with proper cleanup
        from src.core.auth import ApiKeyAuthMiddleware

        original_method = ApiKeyAuthMiddleware._validate_api_key

        try:
            ApiKeyAuthMiddleware._validate_api_key = mock_validate_api_key

            response = client.get(
                "/protected", headers={"X-API-Key": "sk_live_" + "a" * 56}
            )
            assert response.status_code == 200
        finally:
            # Restore the original method
            ApiKeyAuthMiddleware._validate_api_key = original_method

    @patch("src.core.auth.get_supabase_client")
    async def test_api_key_not_found(self, mock_get_client, client):
        """API key not found in database should return 401."""
        # Setup mock client
        mock_client = AsyncMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock the query builder chain
        query_builder = MagicMock()
        query_builder.select = MagicMock(return_value=query_builder)
        query_builder.eq = MagicMock(return_value=query_builder)

        # Mock empty result
        mock_result = MagicMock()
        mock_result.data = []
        mock_result.count = 0
        query_builder.execute = MagicMock(return_value=mock_result)

        mock_client.from_.return_value = query_builder

        try:
            response = client.get(
                "/protected", headers={"X-API-Key": "sk_live_" + "a" * 56}
            )
            assert False, f"Expected 401 but got {response.status_code}"
        except Exception as e:
            from fastapi.exceptions import HTTPException

            if isinstance(e, HTTPException) and e.status_code == 401:
                assert True  # This is expected
            else:
                raise  # Re-raise if it's not the expected exception

    @patch("src.core.auth.get_supabase_client")
    async def test_inactive_api_key(self, mock_get_client, client):
        """Inactive API key should return 401."""
        # Setup mock client
        mock_client = AsyncMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock the query builder chain
        query_builder = MagicMock()
        query_builder.select = MagicMock(return_value=query_builder)
        query_builder.eq = MagicMock(return_value=query_builder)

        # Mock inactive key
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "test-uuid",
                "key_hash": "$2b$12$test_hash",
                "is_active": False,
                "allowed_ips": None,
            }
        ]
        mock_result.count = 1
        query_builder.execute = MagicMock(return_value=mock_result)

        mock_client.from_.return_value = query_builder

        with patch("src.schemas.api_keys.verify_api_key", return_value=True):
            try:
                response = client.get(
                    "/protected", headers={"X-API-Key": "sk_live_" + "a" * 56}
                )
                assert False, f"Expected 401 but got {response.status_code}"
            except Exception as e:
                from fastapi.exceptions import HTTPException

                if isinstance(e, HTTPException) and e.status_code == 401:
                    assert True  # This is expected
                else:
                    raise  # Re-raise if it's not the expected exception

    @patch("src.core.auth.get_supabase_client")
    async def test_ip_not_allowed(self, mock_get_client, client):
        """Request from non-allowed IP should return 401."""
        # Setup mock client
        mock_client = AsyncMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock the query builder chain
        query_builder = MagicMock()
        query_builder.select = MagicMock(return_value=query_builder)
        query_builder.eq = MagicMock(return_value=query_builder)

        # Mock key with IP restrictions
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "test-uuid",
                "key_hash": "$2b$12$test_hash",
                "is_active": True,
                "allowed_ips": ["192.168.1.0/24"],
            }
        ]
        mock_result.count = 1
        query_builder.execute = MagicMock(return_value=mock_result)

        mock_client.from_.return_value = query_builder

        with patch("src.schemas.api_keys.verify_api_key", return_value=True):
            try:
                response = client.get(
                    "/protected", headers={"X-API-Key": "sk_live_" + "a" * 56}
                )
                assert False, f"Expected 401 but got {response.status_code}"
            except Exception as e:
                from fastapi.exceptions import HTTPException

                if isinstance(e, HTTPException) and e.status_code == 401:
                    assert True  # This is expected
                else:
                    raise  # Re-raise if it's not the expected exception

    @patch("src.core.auth.get_supabase_client")
    async def test_database_error_handling(self, mock_get_client, client):
        """Database errors should be handled gracefully and return 401."""
        # Setup mock client that raises an exception
        mock_client = AsyncMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Set up the async chain to raise an exception
        async def mock_execute_error():
            raise Exception("Database error")

        mock_client.table.return_value.select.return_value.eq.return_value.execute = (
            mock_execute_error
        )

        try:
            response = client.get(
                "/protected", headers={"X-API-Key": "sk_live_" + "a" * 56}
            )
            assert False, f"Expected 401 but got {response.status_code}"
        except Exception as e:
            from fastapi.exceptions import HTTPException

            if isinstance(e, HTTPException) and e.status_code == 401:
                assert (
                    True
                )  # Database errors should be treated as invalid keys for security
            else:
                raise  # Re-raise if it's not the expected exception

    async def test_get_client_ip_with_forwarded(self, auth_middleware):
        """Test IP extraction with X-Forwarded-For header."""
        request = MagicMock()
        request.headers.get = MagicMock(
            side_effect=lambda key: {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}.get(
                key
            )
        )
        request.client.host = "127.0.0.1"

        ip = auth_middleware._get_client_ip(request)
        assert ip == "192.168.1.1"

    async def test_get_client_ip_fallback(self, auth_middleware):
        """Test IP extraction fallback to client.host."""
        request = MagicMock()
        request.headers = {}
        request.client.host = "127.0.0.1"

        ip = auth_middleware._get_client_ip(request)
        assert ip == "127.0.0.1"

    async def test_is_exempt_path_health(self, auth_middleware):
        """Health endpoints should be exempt."""
        assert auth_middleware._is_exempt_path("/health")
        assert auth_middleware._is_exempt_path("/health/")

    async def test_is_exempt_path_metrics(self, auth_middleware):
        """Metrics endpoints should be exempt."""
        assert auth_middleware._is_exempt_path("/metrics")
        assert auth_middleware._is_exempt_path("/metrics/")

    @patch.dict("os.environ", {"ENVIRONMENT": "development"})
    async def test_is_exempt_path_docs_dev(self, auth_middleware):
        """Docs should be exempt in development."""
        assert auth_middleware._is_exempt_path("/docs")
        assert auth_middleware._is_exempt_path("/openapi.json")

    async def test_is_exempt_path_docs_prod(self, auth_middleware):
        """Docs should NOT be exempt in production."""
        from unittest.mock import patch, MagicMock

        # Mock settings to return production environment
        mock_settings = MagicMock()
        mock_settings.is_production = True

        with patch("src.core.auth.get_settings", return_value=mock_settings):
            assert not auth_middleware._is_exempt_path("/docs")
            assert not auth_middleware._is_exempt_path("/openapi.json")
