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

  # OpenRouter
  OPENROUTER_API_KEY: str | None = None

  model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

print(f"Using database URL: {settings.DATABASE_URL}")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create engine based on test mode
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG
)

AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Dependency for getting database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
