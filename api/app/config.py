"""
Configuration module combining app settings and database setup.
"""
from typing import List, Generator
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class Settings(BaseSettings):
  """Application settings with validation."""

  # API
  API_PREFIX: str = "/api"
  PROJECT_NAME: str = "Projects API"
  VERSION: str = "1.0.0"
  DEBUG: bool = False

  # Database
  DATABASE_URL: PostgresDsn
  POSTGRES_MAX_CONNECTIONS: int = 100

  # CORS - Always allow all origins in development
  BACKEND_CORS_ORIGINS: List[str] = ["*"]

  # Test mode flag
  TEST_MODE: bool = False

  model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

# Create engine based on test mode
engine = create_engine(
    str(settings.DATABASE_URL).replace("+asyncpg", ""),
    echo=settings.DEBUG
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
