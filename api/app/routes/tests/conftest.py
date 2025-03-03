"""Test fixtures for routes."""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from uuid import uuid4
import os
import asyncio

from ...main import app
from app.models.base import Base
from ...services.openrouter import get_openrouter
from ...config import get_db
from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from ...schemas.project import ProjectCreate
from ...crud import projects, versions

# Use a file-based SQLite database instead of in-memory for test session persistence
TEST_DB_FILE = "test_routes.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="function", autouse=True)
def event_loop():
    """Create a function-scoped event loop for tests.
    
    Using function scope with autouse=True prevents the
    "RuntimeError: Task got Future attached to a different loop" issue
    that occurs when mixing pytest-asyncio with SQLAlchemy async sessions.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()
    asyncio.set_event_loop(None)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database(event_loop):
    """Set up the test database.
    
    We use scope="function" to ensure consistent event loop behavior.
    Using a file-based SQLite database ensures persistence between connections.
    """
    # Remove any existing test database file
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    
    # Create all the tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Explicitly commit the changes
        await conn.commit()
        
    yield
    
    # Clean up after all tests
    await engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

@pytest_asyncio.fixture
async def db_session():
    """Create a test database session with transaction isolation."""
    session = TestingSessionLocal()
    await session.begin()
    
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()

@pytest.fixture
def test_project():
    """Create a test project object."""
    return ProjectCreate(
        name="Test Project",
        description="Test Description"
    )

@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter service for testing."""
    # Create a mock service directly
    mock_service = AsyncMock()
    
    # Default behavior for get_file_changes returns an empty list of changes
    mock_service.get_file_changes.return_value = []
    
    # Override the dependency
    async def get_mock_service():
        return mock_service
    
    # Store original dependency
    original = app.dependency_overrides.get(get_openrouter)
    
    # Override dependency
    app.dependency_overrides[get_openrouter] = get_mock_service
    
    yield mock_service
    
    # Restore original state
    if original:
        app.dependency_overrides[get_openrouter] = original
    else:
        app.dependency_overrides.pop(get_openrouter, None)

@pytest_asyncio.fixture
async def client(db_session):
    """Test client with test database session."""
    # Create an override function for get_db
    async def override_get_db():
        yield db_session
    
    # Store original dependency
    original = app.dependency_overrides.get(get_db)
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create the test client
    with TestClient(app) as client:
        yield client
    
    # Restore original dependency
    if original:
        app.dependency_overrides[get_db] = original
    else:
        app.dependency_overrides.pop(get_db, None)
