"""Tests for core configuration."""

import pytest
from unittest.mock import patch
import os

from src.core.config import Settings, get_settings


@pytest.mark.unit
class TestSettings:
    """Test the Settings class."""

    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        # Just test that we can create a Settings instance
        settings = Settings()

        # API settings should have expected values
        assert settings.api_title == "Language Quiz Service"
        assert (
            settings.api_description
            == "AI-powered language learning quiz generation service"
        )
        assert settings.api_version == "1.0.0"

        # Server settings should have expected values
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000

        # Environment settings should have expected values
        assert isinstance(settings.cors_origins, list)

        # Should have all required fields
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "supabase_url")

    def test_environment_overrides(self):
        """Test that environment variables override defaults."""
        env_vars = {
            "WEB_HOST": "127.0.0.1",
            "WEB_PORT": "9000",
            "ENVIRONMENT": "production",
            "DEBUG": "true",
            "CORS_ORIGINS": '["http://localhost:3000"]',
            "OPENAI_API_KEY": "custom_key",
            "SUPABASE_URL": "https://custom.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "custom_service_key",
            "SUPABASE_ANON_KEY": "custom_anon_key",
            "SUPABASE_PROJECT_REF": "custom_ref",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            # Test overrides
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000
            assert settings.environment == "production"
            assert settings.debug is True
            assert settings.cors_origins == ["http://localhost:3000"]
            assert settings.openai_api_key == "custom_key"
            assert settings.supabase_url == "https://custom.supabase.co"
            assert settings.supabase_key == "custom_service_key"
            assert settings.supabase_anon_key == "custom_anon_key"
            assert settings.supabase_project_ref == "custom_ref"

    def test_is_production_property(self):
        """Test the is_production property."""
        # Create a settings instance and test the property
        settings = Settings()

        # Test with different environment values
        settings.environment = "development"
        assert settings.is_production is False

        settings.environment = "production"
        assert settings.is_production is True

        settings.environment = "staging"
        assert settings.is_production is False

    def test_cors_origins_list(self):
        """Test CORS origins configuration."""
        settings = Settings()

        # Should be a list
        assert isinstance(settings.cors_origins, list)

        # Can set different values
        settings.cors_origins = ["http://localhost:3000", "https://example.com"]
        assert settings.cors_origins == ["http://localhost:3000", "https://example.com"]


@pytest.mark.unit
class TestGetSettings:
    """Test the get_settings function."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
        assert isinstance(settings1, Settings)

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)


@pytest.mark.unit
class TestConfigurationIntegration:
    """Test configuration integration scenarios."""

    def test_settings_work_with_fastapi(self):
        """Test that settings can be used with FastAPI dependencies."""
        # This test verifies that the settings can be injected into FastAPI
        settings = get_settings()

        # Should be able to access all required fields
        assert hasattr(settings, "api_title")
        assert hasattr(settings, "api_version")
        assert hasattr(settings, "host")
        assert hasattr(settings, "port")
        assert hasattr(settings, "cors_origins")
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "supabase_url")
        assert hasattr(settings, "supabase_key")

    def test_required_fields_for_production(self):
        """Test that required fields are properly configured for production."""
        settings = Settings()

        # Should have all required fields
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "supabase_url")
        assert hasattr(settings, "supabase_key")
        assert hasattr(settings, "supabase_anon_key")
        assert hasattr(settings, "supabase_project_ref")

        # Test the is_production property
        original_env = settings.environment
        settings.environment = "production"
        assert settings.is_production is True
        settings.environment = original_env
