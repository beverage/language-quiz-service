"""Core configuration settings."""

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.
    """

    # General settings
    log_level: str = "INFO"

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


# Singleton instance
settings = Settings()
