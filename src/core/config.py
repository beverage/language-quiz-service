"""Core configuration settings."""

from typing import List
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
    cors_origins: List[str] = Field(default=["*"])

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # OpenAI API settings
    openai_api_key: str = Field(default="test_key", alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4-turbo-preview"

    # Supabase settings
    supabase_url: str = Field(default="http://test.supabase.co", alias="SUPABASE_URL")
    supabase_key: str = Field(default="test_key", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str = Field(default="test_key", alias="SUPABASE_ANON_KEY")
    supabase_project_ref: str = Field(default="test_ref", alias="SUPABASE_PROJECT_REF")

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Get the settings instance."""
    return settings
