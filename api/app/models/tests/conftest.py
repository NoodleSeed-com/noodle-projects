"""Test fixtures for models."""
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from ...models.base import Base
from ...config import settings

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
    return engine

@pytest_asyncio.fixture(scope="module")
async def test_db(test_engine):
    """Create test database session."""
    # Drop all tables with CASCADE before SQLAlchemy drop_all
    async with test_engine.connect() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        await conn.commit()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestingSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(test_db: AsyncSession):
    """Provide database session that rolls back after each test."""
    async with test_db.begin_nested() as nested:  # Create savepoint
        yield test_db
        await nested.rollback()  # Rollback to savepoint
