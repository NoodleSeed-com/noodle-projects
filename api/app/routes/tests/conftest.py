"""Test fixtures for routes."""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import uuid4
import os
import asyncio

from ...main import app
from app.models.base import Base
from ...services.openrouter import get_openrouter
from ...config import get_db
from ...models.project import Project, ProjectCreate
from ...models.version import Version
from ...models.file import File
from ...crud import projects, versions

# Import the event_loop fixture from the centralized fixtures
from ...tests.fixtures.db import event_loop, db_session as base_db_session

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
async def client(base_db_session):
    """Test client with test database session."""
    # Create an override function for get_db
    async def override_get_db():
        yield base_db_session
    
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
        
    # Make db_session available to tests that expect it with original name
    
@pytest.fixture
def db_session(base_db_session):
    """Alias base_db_session as db_session for backward compatibility."""
    return base_db_session