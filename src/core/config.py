"""Core configuration settings."""

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.
    """

    # General settings
    log_level: str = "INFO"

    # FastAPI settings
    api_title: str = "Language Quiz Service"
    api_description: str = "AI-powered language learning quiz generation service"
    api_version: str = "1.0.0"

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="WEB_HOST")
    port: int = Field(default=8000, alias="WEB_PORT")

    # Security & CORS
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins (comma-separated in env: CORS_ORIGINS)",
    )

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100, description="Requests per minute per IP"
    )
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Authentication settings
    require_auth: bool = Field(
        default=True,
        alias="REQUIRE_AUTH",
        description="Require authentication (default: true for security)",
    )

    # OpenAI API settings
    openai_api_key: str = Field(default="test_key", alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4-turbo-preview"

    # Supabase settings
    supabase_url: str = Field(default="http://test.supabase.co", alias="SUPABASE_URL")
    supabase_key: str = Field(default="test_key", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str = Field(default="test_key", alias="SUPABASE_ANON_KEY")
    supabase_project_ref: str = Field(default="test_ref", alias="SUPABASE_PROJECT_REF")

    # Observability - Grafana Cloud (OpenTelemetry)
    grafana_cloud_instance_id: str | None = Field(
        default=None, alias="GRAFANA_CLOUD_INSTANCE_ID"
    )
    grafana_cloud_api_key: str | None = Field(
        default=None, alias="GRAFANA_CLOUD_API_KEY"
    )
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
        description="OpenTelemetry OTLP endpoint (e.g., Grafana Cloud)",
    )

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev", "local")

    @property
    def should_require_auth(self) -> bool:
        """Determine if authentication should be required."""
        return self.require_auth or self.is_production or self.is_staging

    @property
    def production_cors_origins(self) -> list[str]:
        """
        Get CORS origins appropriate for the current environment.

        In staging/production: REQUIRES explicit CORS_ORIGINS configuration.
        In development: Uses configured cors_origins (defaults to ["*"]).

        Raises:
            ValueError: If CORS_ORIGINS is not explicitly set in staging/production.
        """
        if self.is_production or self.is_staging:
            # REQUIRE explicit configuration in staging/production
            if self.cors_origins == ["*"]:
                raise ValueError(
                    f"CORS_ORIGINS must be explicitly configured in {self.environment} environment. "
                    "Set CORS_ORIGINS environment variable to allowed domains, e.g.: "
                    'CORS_ORIGINS=\'["https://example.com","https://www.example.com"]\''
                )
            return self.cors_origins

        # Development: allow default (["*"])
        return self.cors_origins


# Singleton instance - initialized lazily
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the settings instance (useful for testing)."""
    global _settings
    _settings = None


# For backward compatibility, create a property that behaves like the old singleton
def __getattr__(name):
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
