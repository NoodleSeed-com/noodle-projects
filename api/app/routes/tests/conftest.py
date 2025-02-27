"""Test fixtures for routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from uuid import uuid4

from ...main import app
from ...models.base import Base
from ...services.openrouter import get_openrouter
from ...config import get_db
from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from ...schemas.project import ProjectCreate
from ...crud import projects, versions

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture
async def setup_database():
    """Set up the test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_database):
    """Create a test database session."""
    async with TestingSessionLocal() as session:
        # Start with a clean session - commit any pending data
        await session.commit()
        yield session

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

@pytest.fixture
def client(db_session):
    """Test client with test database session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
