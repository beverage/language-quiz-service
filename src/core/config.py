"""Core configuration settings."""
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    
    # Supabase  
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_project_ref: str = Field(..., alias="SUPABASE_PROJECT_REF")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Singleton instance
settings = Settings() 