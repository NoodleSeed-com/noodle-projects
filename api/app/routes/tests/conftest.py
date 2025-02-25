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
    mock = MagicMock()
    mock.get_file_changes = AsyncMock(return_value=[])
    
    async def mock_service():
        return mock
    
    app.dependency_overrides[get_openrouter] = mock_service
    yield mock
    app.dependency_overrides.clear()

@pytest.fixture
def client(db_session):
    """Test client with test database session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
