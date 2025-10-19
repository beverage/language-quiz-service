"""Tests for endpoint access control middleware."""

import pytest

from src.core.config import Settings

# Test constants
TEST_CORS_ORIGIN = "https://example.com"


class TestEndpointAccessControl:
    """Test endpoint access control logic in different environments."""

    def test_development_environment_detected(self):
        """Test that development environment is correctly identified."""
        settings = Settings(environment="development")

        assert settings.is_development is True
        assert settings.is_staging is False
        assert settings.is_production is False

    def test_staging_environment_detected(self):
        """Test that staging environment is correctly identified."""
        settings = Settings(environment="staging", cors_origins=[TEST_CORS_ORIGIN])

        assert settings.is_staging is True
        assert settings.is_development is False
        assert settings.is_production is False

    def test_production_environment_detected(self):
        """Test that production environment is correctly identified."""
        settings = Settings(environment="production", cors_origins=[TEST_CORS_ORIGIN])

        assert settings.is_production is True
        assert settings.is_development is False
        assert settings.is_staging is False

    def test_staging_requires_authentication(self):
        """Test that staging requires authentication like production."""
        settings = Settings(
            environment="staging",
            cors_origins=[TEST_CORS_ORIGIN],
            require_auth=False,  # Explicitly set to False
        )

        # should_require_auth should override and return True for staging
        assert settings.should_require_auth is True

    def test_production_requires_authentication(self):
        """Test that production requires authentication."""
        settings = Settings(
            environment="production",
            cors_origins=[TEST_CORS_ORIGIN],
            require_auth=False,  # Explicitly set to False
        )

        # should_require_auth should override and return True for production
        assert settings.should_require_auth is True
