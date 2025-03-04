"""
Configuration module for application settings.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings with validation."""

    # API
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "Projects API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # CORS - Always allow all origins in development
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Test mode flag
    TEST_MODE: bool = False

    # OpenRouter
    OPENROUTER_API_KEY: str | None = None
    
    # Template path - path to project templates
    TEMPLATE_PATH: str = "api/templates"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

if settings.DEBUG:
    print(f"Using Supabase URL: {settings.SUPABASE_URL}")