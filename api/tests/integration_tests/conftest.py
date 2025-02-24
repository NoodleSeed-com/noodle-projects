import os
import pytest
import pytest_asyncio
from pathlib import Path
from dotenv import load_dotenv
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import asyncio

# Load environment variables before importing app modules
env_path = Path(__file__).parent / "test.env"
load_dotenv(dotenv_path=env_path)

# Import app modules after environment is configured
from app.main import app
from app.config import get_db, settings
from app.models.base import Base

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine(event_loop):
    """Create a session-scoped SQLAlchemy engine."""
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="session")
async def async_session_factory(test_engine):
    """Create a session factory."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function")
async def db_session(async_session_factory):
    """Create a function-scoped database session with transaction."""
    async with async_session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client with a function-scoped database session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def test_project():
    """Fixture for test project data."""
    return {
        "name": "Test Project",
        "description": "This is a test project"
    }

@pytest.fixture
def test_version():
    """Fixture for test version data."""
    return {
        "version_number": 1,
        "name": "Test Version",
        "parent_id": None
    }

@pytest.fixture
def test_files():
    """Fixture for test file data."""
    return [
        {
            "path": "src/main.py",
            "content": "print('Hello, World!')"
        },
        {
            "path": "README.md",
            "content": "# Test Project\nThis is a test."
        }
    ]
