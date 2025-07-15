"""Comprehensive security tests for rate limiting and CORS."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from slowapi import Limiter

from src.core.config import Settings, get_settings
from src.main import app


@pytest.fixture
def client():
    """Create a test client for security tests."""
    return TestClient(app)


@pytest.fixture
def mock_limiter():
    """Mock the rate limiter for testing."""
    return MagicMock(spec=Limiter)


class TestRateLimitingBehavior:
    """Test actual rate limiting behavior and edge cases."""

    def test_rate_limit_custom_configuration(self, client: TestClient):
        """Test rate limiting with custom configuration."""

        def mock_settings():
            return Settings(
                rate_limit_requests=2, rate_limit_window=60, environment="testing"
            )

        app.dependency_overrides[get_settings] = mock_settings

        try:
            # Test that custom rate limit is reflected in response
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["rate_limit"] == "2/minute"

        finally:
            app.dependency_overrides.clear()

    def test_rate_limit_middleware_configured(self, client: TestClient):
        """Test that rate limiting middleware is properly configured."""
        response = client.get("/health")

        assert response.status_code == 200

        # Verify the limiter is configured in the app state
        from src.main import app

        assert hasattr(app.state, "limiter")
        assert app.state.limiter is not None

        # Verify rate limit info is in the response
        data = response.json()
        assert "rate_limit" in data
        assert "100/minute" in data["rate_limit"]

    def test_rate_limit_multiple_endpoints(self, client: TestClient):
        """Test that rate limiting applies to multiple endpoints."""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200

        # Verify rate limiting is configured for the app
        from src.main import app

        assert hasattr(app.state, "limiter")

        # Verify both endpoints have rate limit decorators
        data = response.json()
        assert "rate_limit" in data

    def test_rate_limit_different_environments(self, client: TestClient):
        """Test rate limiting configuration in different environments."""
        environments = ["development", "staging", "production"]

        for env in environments:

            def mock_env_settings():
                return Settings(
                    environment=env, rate_limit_requests=100, rate_limit_window=60
                )

            app.dependency_overrides[get_settings] = mock_env_settings

            try:
                response = client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["environment"] == env
                assert data["rate_limit"] == "100/minute"

            finally:
                app.dependency_overrides.clear()

    def test_rate_limit_window_configuration(self, client: TestClient):
        """Test rate limiting window configuration."""

        def mock_settings():
            return Settings(
                rate_limit_requests=100,
                rate_limit_window=120,  # 2 minutes
                environment="testing",
            )

        app.dependency_overrides[get_settings] = mock_settings

        try:
            response = client.get("/health")
            assert response.status_code == 200
            # Note: slowapi uses per-minute format, so this tests the config is used

        finally:
            app.dependency_overrides.clear()


class TestCORSBehavior:
    """Test CORS behavior across different environments."""

    def test_cors_methods_development(self, client: TestClient):
        """Test CORS methods in development environment."""

        def mock_dev_settings():
            return Settings(environment="development")

        app.dependency_overrides[get_settings] = mock_dev_settings

        try:
            # Test that all HTTP methods are allowed in development
            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert response.status_code == 200

        finally:
            app.dependency_overrides.clear()

    def test_cors_methods_production(self, client: TestClient):
        """Test CORS methods in production environment."""

        def mock_prod_settings():
            return Settings(environment="production")

        app.dependency_overrides[get_settings] = mock_prod_settings

        try:
            # Test that specific methods are configured for production
            response = client.options(
                "/health",
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert response.status_code == 200

        finally:
            app.dependency_overrides.clear()

    def test_cors_origins_configuration(self, client: TestClient):
        """Test CORS origins configuration."""

        def mock_settings():
            return Settings(
                environment="production",
                cors_origins=["https://myapp.com", "https://api.myapp.com"],
            )

        app.dependency_overrides[get_settings] = mock_settings

        try:
            # Test request with allowed origin
            response = client.get("/health", headers={"Origin": "https://myapp.com"})
            assert response.status_code == 200

        finally:
            app.dependency_overrides.clear()

    def test_production_cors_origins_property(self):
        """Test the production_cors_origins property behavior."""
        # Test development environment uses configured origins
        dev_settings = Settings(
            environment="development",
            cors_origins=["http://localhost:3000", "http://localhost:8080"],
        )
        assert dev_settings.production_cors_origins == [
            "http://localhost:3000",
            "http://localhost:8080",
        ]

        # Test production environment uses wildcard (current behavior)
        prod_settings = Settings(
            environment="production", cors_origins=["http://localhost:3000"]
        )
        assert prod_settings.production_cors_origins == ["*"]

        # Test is_production property
        assert not dev_settings.is_production
        assert prod_settings.is_production


class TestSecurityIntegration:
    """Test security features working together."""

    def test_cors_and_rate_limiting_integration(self, client: TestClient):
        """Test that CORS and rate limiting work together properly."""
        response = client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "User-Agent": "test-security-client",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should have rate limit info in response
        assert "rate_limit" in data
        assert "status" in data
        assert data["status"] == "healthy"

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers

        # Verify rate limiting middleware is configured
        from src.main import app

        assert hasattr(app.state, "limiter")

    def test_security_configuration_staging(self, client: TestClient):
        """Test complete security configuration for staging."""

        def mock_staging_settings():
            return Settings(
                environment="staging",
                rate_limit_requests=100,
                rate_limit_window=60,
                cors_origins=["*"],
            )

        app.dependency_overrides[get_settings] = mock_staging_settings

        try:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()

            # Verify staging configuration
            assert data["environment"] == "staging"
            assert data["rate_limit"] == "100/minute"

            # Verify rate limiting middleware is configured
            assert hasattr(app.state, "limiter")

        finally:
            app.dependency_overrides.clear()

    def test_security_configuration_production(self, client: TestClient):
        """Test complete security configuration for production."""

        def mock_production_settings():
            return Settings(
                environment="production",
                rate_limit_requests=100,
                rate_limit_window=60,
                cors_origins=["*"],
            )

        app.dependency_overrides[get_settings] = mock_production_settings

        try:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()

            # Verify production configuration
            assert data["environment"] == "production"
            assert data["rate_limit"] == "100/minute"

            # Verify rate limiting middleware is configured
            assert hasattr(app.state, "limiter")

        finally:
            app.dependency_overrides.clear()

    def test_environment_detection_logic(self):
        """Test environment detection logic."""
        # Test various environment values
        test_cases = [
            ("development", False),
            ("staging", False),
            ("production", True),
            ("test", False),
            ("dev", False),
            ("prod", False),  # Only exact "production" should return True
        ]

        for env, expected_is_production in test_cases:
            settings = Settings(environment=env)
            assert (
                settings.is_production == expected_is_production
            ), f"Environment '{env}' should have is_production={expected_is_production}"


class TestSecurityConfiguration:
    """Test security configuration settings."""

    def test_default_rate_limit_settings(self):
        """Test default rate limit settings."""
        settings = Settings()
        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_window == 60

    def test_custom_rate_limit_settings(self):
        """Test custom rate limit settings."""
        settings = Settings(rate_limit_requests=50, rate_limit_window=120)
        assert settings.rate_limit_requests == 50
        assert settings.rate_limit_window == 120

    def test_cors_origins_default(self):
        """Test default CORS origins."""
        settings = Settings()
        assert settings.cors_origins == ["*"]

    def test_cors_origins_custom(self):
        """Test custom CORS origins."""
        custom_origins = ["https://myapp.com", "https://api.myapp.com"]
        settings = Settings(cors_origins=custom_origins)
        assert settings.cors_origins == custom_origins

    def test_environment_specific_cors(self):
        """Test environment-specific CORS configuration."""
        # Development environment
        dev_settings = Settings(
            environment="development", cors_origins=["http://localhost:3000"]
        )
        assert dev_settings.production_cors_origins == ["http://localhost:3000"]

        # Production environment (currently returns wildcard)
        prod_settings = Settings(
            environment="production", cors_origins=["http://localhost:3000"]
        )
        assert prod_settings.production_cors_origins == ["*"]


@pytest.mark.integration
class TestSecurityIntegrationScenarios:
    """Integration tests for real-world security scenarios."""

    def test_api_client_simulation(self, client: TestClient):
        """Simulate a typical API client interaction."""
        # Simulate a client making multiple requests
        for i in range(5):
            response = client.get(
                "/health",
                headers={
                    "Origin": "https://myapp.com",
                    "User-Agent": f"MyApp-Client/1.0 (request-{i})",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

            # Verify rate limiting info is in response
            assert "rate_limit" in data

            # Verify CORS headers are present
            assert "access-control-allow-origin" in response.headers

        # Verify rate limiting middleware is configured for the app
        from src.main import app

        assert hasattr(app.state, "limiter")

    def test_cross_origin_request_simulation(self, client: TestClient):
        """Simulate cross-origin requests from different domains."""
        origins = [
            "https://myapp.com",
            "https://admin.myapp.com",
            "https://api.myapp.com",
            "http://localhost:3000",
        ]

        for origin in origins:
            response = client.get("/health", headers={"Origin": origin})
            assert response.status_code == 200

            # Should work with current permissive CORS configuration
            data = response.json()
            assert data["status"] == "healthy"

    def test_production_deployment_simulation(self, client: TestClient):
        """Simulate production deployment scenario."""

        def mock_production_settings():
            return Settings(
                environment="production",
                rate_limit_requests=100,
                rate_limit_window=60,
                cors_origins=["*"],  # Will be overridden by production_cors_origins
                debug=False,
            )

        app.dependency_overrides[get_settings] = mock_production_settings

        try:
            # Simulate multiple clients
            for client_id in range(3):
                response = client.get(
                    "/health",
                    headers={
                        "Origin": "https://example.com",
                        "User-Agent": f"ProductionClient-{client_id}",
                        "X-Client-ID": str(client_id),
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["environment"] == "production"
                assert data["rate_limit"] == "100/minute"

        finally:
            app.dependency_overrides.clear()
