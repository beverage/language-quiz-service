"""
Environment configuration using pydantic settings.

Simple configuration for Phase 1: OPENAI_API_KEY + future supabase settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application settings - Phase 1: OpenAI + future Supabase configuration."""
    
    # Current requirement
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    
    # Future Phase 1: Supabase settings (to be added)
    # supabase_url: str = Field(..., alias="SUPABASE_URL")
    # supabase_key: str = Field(..., alias="SUPABASE_ANON_KEY") 
    # supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    # supabase_project_ref: str = Field(..., alias="SUPABASE_PROJECT_REF")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Singleton instance for global access
app_settings = AppSettings() 