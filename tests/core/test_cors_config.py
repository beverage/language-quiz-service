"""Tests for CORS configuration validation."""

import pytest

from src.core.config import Settings

# Test constants
VALID_CORS_ORIGINS = ["https://example.com", "https://www.example.com"]


class TestCORSConfiguration:
    """Test CORS configuration validation in different environments."""

    def test_development_allows_wildcard_cors(self):
        """In development, wildcard CORS should be allowed."""
        settings = Settings(environment="development")

        cors_origins = settings.production_cors_origins

        assert cors_origins == ["*"]

    def test_staging_requires_explicit_cors(self):
        """In staging, explicit CORS origins must be configured."""
        settings = Settings(environment="staging")  # Default cors_origins = ["*"]

        with pytest.raises(
            ValueError, match="CORS_ORIGINS must be explicitly configured"
        ):
            _ = settings.production_cors_origins

    def test_staging_accepts_explicit_cors(self):
        """In staging, explicitly configured CORS origins should be accepted."""
        settings = Settings(environment="staging", cors_origins=VALID_CORS_ORIGINS)

        cors_origins = settings.production_cors_origins

        assert cors_origins == VALID_CORS_ORIGINS

    def test_production_requires_explicit_cors(self):
        """In production, explicit CORS origins must be configured."""
        settings = Settings(environment="production")  # Default cors_origins = ["*"]

        with pytest.raises(
            ValueError, match="CORS_ORIGINS must be explicitly configured"
        ):
            _ = settings.production_cors_origins

    def test_production_accepts_explicit_cors(self):
        """In production, explicitly configured CORS origins should be accepted."""
        settings = Settings(
            environment="production", cors_origins=["https://example.com"]
        )

        cors_origins = settings.production_cors_origins

        assert cors_origins == ["https://example.com"]

    def test_error_message_provides_example(self):
        """Error message should provide example of correct configuration."""
        settings = Settings(environment="staging")

        with pytest.raises(ValueError) as exc_info:
            _ = settings.production_cors_origins

        error_message = str(exc_info.value)
        assert "CORS_ORIGINS" in error_message
        assert "Set CORS_ORIGINS environment variable" in error_message
