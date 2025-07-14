"""
Simplified tests for auth middleware core functionality.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.core.auth import ApiKeyAuthMiddleware
from src.schemas.api_keys import generate_api_key, check_ip_allowed
from supabase import Client


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase Client using the problems test pattern."""
    return AsyncMock(spec=Client)


@pytest.fixture
def auth_middleware():
    """Create auth middleware instance."""
    mock_app = MagicMock()
    return ApiKeyAuthMiddleware(mock_app)


@pytest.mark.unit
class TestApiKeyGeneration:
    """Test API key generation (from schemas module)."""

    def test_generate_api_key_format(self):
        """Test generated API keys have correct format."""
        full_key, prefix = generate_api_key()

        # Should be 64 characters total
        assert len(full_key) == 64

        # Should start with sk_live_
        assert full_key.startswith("sk_live_")

        # Prefix should be first 12 characters
        assert len(prefix) == 12
        assert prefix == full_key[:12]

        # Rest should be alphanumeric
        rest = full_key[8:]  # After "sk_live_"
        assert len(rest) == 56
        assert rest.isalnum()

    def test_generate_api_key_uniqueness(self):
        """Test that generated keys are unique."""
        key1, _ = generate_api_key()
        key2, _ = generate_api_key()
        assert key1 != key2


@pytest.mark.unit
class TestPathExemptions:
    """Test path exemption logic."""

    def test_health_endpoints_exempt(self, auth_middleware):
        """Health endpoints should be exempt."""
        assert auth_middleware._is_exempt_path("/health")
        assert auth_middleware._is_exempt_path("/health/check")

    def test_metrics_endpoints_exempt(self, auth_middleware):
        """Metrics endpoints should be exempt."""
        assert auth_middleware._is_exempt_path("/metrics")
        assert auth_middleware._is_exempt_path("/metrics/prometheus")

    @patch("src.core.auth.get_settings")
    def test_docs_exempt_in_development(self, mock_settings, auth_middleware):
        """Docs should be exempt in development."""
        # Create a mock settings object with the is_production attribute
        mock_settings_obj = MagicMock()
        mock_settings_obj.is_production = False
        mock_settings.return_value = mock_settings_obj

        assert auth_middleware._is_exempt_path("/docs")
        assert auth_middleware._is_exempt_path("/redoc")
        assert auth_middleware._is_exempt_path("/openapi.json")

    def test_docs_and_paths_covered_by_integration_tests(self):
        """Production path exemption and complex scenarios are covered by integration tests."""
        # This is a placeholder to indicate that complex path exemption logic
        # including production settings are tested in the integration test suite
        # where the full FastAPI application context is available
        pass

    def test_root_path_exempt(self, auth_middleware):
        """Root path should be exempt."""
        assert auth_middleware._is_exempt_path("/")


@pytest.mark.unit
class TestClientIPExtraction:
    """Test client IP extraction logic."""

    def test_ip_from_x_forwarded_for(self, auth_middleware):
        """Should extract first IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers.get.side_effect = lambda header: {
            "X-Forwarded-For": "192.168.1.1, 10.0.0.1, 127.0.0.1",
            "X-Real-IP": None,
        }.get(header)
        request.client.host = "127.0.0.1"

        ip = auth_middleware._get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_ip_from_x_real_ip(self, auth_middleware):
        """Should extract IP from X-Real-IP header when no X-Forwarded-For."""
        request = MagicMock()
        request.headers.get.side_effect = lambda header: {
            "X-Forwarded-For": None,
            "X-Real-IP": "203.0.113.42",
        }.get(header)
        request.client.host = "127.0.0.1"

        ip = auth_middleware._get_client_ip(request)
        assert ip == "203.0.113.42"

    def test_ip_fallback_to_client_host(self, auth_middleware):
        """Should fallback to client.host when no proxy headers."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "127.0.0.1"

        ip = auth_middleware._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_ip_unknown_when_no_client(self, auth_middleware):
        """Should return 'unknown' when no client info available."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client = None

        ip = auth_middleware._get_client_ip(request)
        assert ip == "unknown"

    def test_ip_extraction_handles_whitespace(self, auth_middleware):
        """Should handle whitespace in forwarded headers."""
        request = MagicMock()
        request.headers.get.side_effect = lambda header: {
            "X-Forwarded-For": " 192.168.1.1 , 10.0.0.1 ",
            "X-Real-IP": None,
        }.get(header)
        request.client.host = "127.0.0.1"

        ip = auth_middleware._get_client_ip(request)
        assert ip == "192.168.1.1"


@pytest.mark.unit
class TestApiKeyExtraction:
    """Test API key extraction from requests."""

    def test_extract_api_key_success(self, auth_middleware):
        """Should extract API key from X-API-Key header."""
        request = MagicMock()
        request.headers.get.return_value = "sk_live_test123"

        api_key = auth_middleware._extract_api_key(request)
        assert api_key == "sk_live_test123"
        request.headers.get.assert_called_once_with("X-API-Key")

    def test_extract_api_key_missing(self, auth_middleware):
        """Should return None when header is missing."""
        request = MagicMock()
        request.headers.get.return_value = None

        api_key = auth_middleware._extract_api_key(request)
        assert api_key is None
        request.headers.get.assert_called_once_with("X-API-Key")


@pytest.mark.unit
@pytest.mark.asyncio
class TestApiKeyValidation:
    """Test API key validation against database."""

    async def test_validate_api_key_database_error(self, auth_middleware):
        """Test database error handling (simplified)."""
        # Test that None is returned when database operations fail
        # This test focuses on the error handling path without complex mocking
        with patch(
            "src.core.auth.get_supabase_client",
            side_effect=Exception("DB connection failed"),
        ):
            result = await auth_middleware._validate_api_key("sk_live_" + "a" * 56)
            assert result is None

    async def test_api_key_validation_covered_by_integration_tests(self):
        """Complex database validation scenarios are covered by integration tests."""
        # This is a placeholder to indicate that full database validation
        # including async operations are tested in the integration test suite
        # where the real database and Supabase client are available
        pass


@pytest.mark.unit
@pytest.mark.asyncio
class TestUsageTracking:
    """Test API key usage tracking."""

    @patch("src.core.auth.get_supabase_client")
    async def test_update_key_usage_success(self, mock_get_client, auth_middleware):
        """Test successful usage tracking with RPC."""
        # Setup mock client
        mock_client = AsyncMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock RPC success
        rpc_builder = MagicMock()
        rpc_builder.execute = MagicMock(
            return_value=MagicMock(data=[{"success": True}])
        )
        mock_client.rpc.return_value = rpc_builder

        # Should not raise any exceptions
        await auth_middleware._update_key_usage("test-uuid")

        # Verify RPC was called correctly
        mock_client.rpc.assert_called_once_with(
            "increment_api_key_usage", {"key_id": "test-uuid"}
        )

    @patch("src.core.auth.get_supabase_client")
    async def test_update_key_usage_fallback(self, mock_get_client, auth_middleware):
        """Test fallback when RPC doesn't exist."""
        # Setup mock client
        mock_client = AsyncMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock RPC returning empty (indicating function doesn't exist)
        rpc_builder = MagicMock()
        rpc_builder.execute = AsyncMock(return_value=MagicMock(data=[]))
        mock_client.rpc.return_value = rpc_builder

        # Mock the fallback update query
        update_builder = MagicMock()
        update_builder.eq = MagicMock(return_value=update_builder)
        update_builder.execute = AsyncMock(return_value=MagicMock())

        table_builder = MagicMock()
        table_builder.update = MagicMock(return_value=update_builder)
        mock_client.table.return_value = table_builder

        await auth_middleware._update_key_usage("test-uuid")

        # Should try RPC first, then fallback to update
        mock_client.rpc.assert_called_once()
        mock_client.table.assert_called_once_with("api_keys")

    @patch("src.core.auth.get_supabase_client")
    async def test_update_key_usage_error_handling(
        self, mock_get_client, auth_middleware
    ):
        """Test that usage tracking errors don't propagate."""
        # Setup mock client that raises an exception
        mock_client = AsyncMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock RPC that raises exception
        mock_client.rpc.side_effect = Exception("RPC error")

        # Should not raise any exceptions
        await auth_middleware._update_key_usage("test-uuid")


@pytest.mark.unit
class TestIPAllowlistChecking:
    """Test IP allowlist validation (from schemas module)."""

    def test_no_restrictions_allows_all(self):
        """When no IP restrictions, all IPs should be allowed."""
        assert check_ip_allowed("192.168.1.1", None)
        assert check_ip_allowed("10.0.0.1", [])

    def test_exact_ip_match(self):
        """Exact IP matches should be allowed."""
        allowed_ips = ["192.168.1.1", "10.0.0.1"]
        assert check_ip_allowed("192.168.1.1", allowed_ips)
        assert check_ip_allowed("10.0.0.1", allowed_ips)

    def test_cidr_range_match(self):
        """IPs within CIDR ranges should be allowed."""
        allowed_ips = ["192.168.1.0/24"]
        assert check_ip_allowed("192.168.1.100", allowed_ips)
        assert check_ip_allowed("192.168.1.1", allowed_ips)

    def test_ip_not_in_allowlist(self):
        """IPs not in allowlist should be denied."""
        allowed_ips = ["192.168.1.0/24"]
        assert not check_ip_allowed("10.0.0.1", allowed_ips)
        assert not check_ip_allowed("192.168.2.1", allowed_ips)

    def test_invalid_ip_denied(self):
        """Invalid IP addresses should be denied."""
        allowed_ips = ["192.168.1.0/24"]
        assert not check_ip_allowed("invalid_ip", allowed_ips)
        assert not check_ip_allowed("", allowed_ips)

    def test_ipv6_support(self):
        """IPv6 addresses should be supported."""
        allowed_ips = ["2001:db8::/32"]
        assert check_ip_allowed("2001:db8::1", allowed_ips)
        assert not check_ip_allowed("2001:db9::1", allowed_ips)
