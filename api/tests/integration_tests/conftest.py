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
from app.services.openrouter import OpenRouterService
from app.schemas.common import FileChange, AIResponse
from typing import List

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
    """Create a function-scoped database session with transaction.
    
    This fixture creates a session with an active transaction, then rolls
    it back at the end of the test to undo any changes.
    """
    # Create a new session for each test
    session = async_session_factory()
    
    # Start a transaction
    await session.begin()
    
    try:
        # Use the session in the test
        yield session
    finally:
        # Rollback the transaction to undo any changes
        await session.rollback()
        # Close the session
        await session.close()

class TestOpenRouterService(OpenRouterService):
    """Test version of OpenRouterService that doesn't call actual API."""
    
    async def get_file_changes(
        self,
        project_context: str,
        change_request: str,
        current_files: List
    ) -> List[FileChange]:
        """Return simple test file changes without calling API."""
        # Return a simple change that creates a new file
        # Using proper operation value from FileOperation enum
        from app.schemas.common import FileOperation
        
        # Create a new file
        return [
            FileChange(
                path="test_file.txt",
                content="This is a test file created for testing",
                operation=FileOperation.CREATE
            )
        ]

@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client with a function-scoped database session.
    
    This uses the db_session fixture which handles transaction management,
    including proper nested transaction support for version creation.
    """    
    # Create a function that will use our existing db_session
    async def override_get_db():
        yield db_session
    
    # Override the OpenRouter service with our test version
    async def get_test_openrouter():
        return TestOpenRouterService()
    
    # Set up overrides
    app.dependency_overrides[get_db] = override_get_db
    from app.services.openrouter import get_openrouter
    app.dependency_overrides[get_openrouter] = get_test_openrouter
    
    # Use trailing slash in base_url to prevent redirect issues
    async with AsyncClient(app=app, base_url="http://test/", follow_redirects=True) as ac:
        yield ac
    
    # Clear all dependency overrides
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
