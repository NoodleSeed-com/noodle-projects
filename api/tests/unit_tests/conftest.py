import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import Column, Table, Select
from sqlalchemy.orm import joinedload

# Load environment variables before importing app modules
env_path = Path(__file__).parent / "test.env"
load_dotenv(dotenv_path=env_path)

# Import app modules after environment is configured
from app.main import app
from app.config import get_db, settings

from datetime import datetime
from uuid import uuid4
from app.models.project import Project
from app.models.version import Version
from app.models.file import File

@pytest.fixture(scope="module")
def mock_project():
    """Mock Project instance for testing."""
    project = Project(
        id=uuid4(),
        name="Test Project",
        description="Test Description",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    project.versions = []  # Initialize empty versions list
    return project

@pytest.fixture(scope="module")
def mock_version(mock_project):
    """Mock Version instance for testing."""
    version = Version(
        id=uuid4(),
        project_id=mock_project.id,
        version_number=0,  # This is correct - initial version is 0
        name="Initial Version",
        parent_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    # First, create version without files to get a version_id
    version_id = version.id
    
    # Initialize files list with the version_id
    version.files = [
        File(
            id=uuid4(),
            version_id=version_id,  # Add version_id parameter here
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    # Set up bidirectional relationships
    for file in version.files:
        file.version_id = version.id
        file.version = version
    
    # Set up project relationship
    version.project = mock_project
    mock_project.versions = [version]
    
    return version

@pytest.fixture(scope="module", params=["projects", "versions"])
def mock_db(request, mock_project, mock_version):
    """Parameterized fixture for different return types."""
    mock = AsyncMock()
    
    # Configure async methods
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    # Configure refresh to set required fields
    async def mock_refresh(obj):
        if not getattr(obj, 'id', None):
            obj.id = uuid4()
        # Only set active on Project instances
        if isinstance(obj, Project) and not getattr(obj, 'active', None):
            obj.active = True
        if not getattr(obj, 'created_at', None):
            obj.created_at = datetime.now()
        if not getattr(obj, 'updated_at', None):
            obj.updated_at = datetime.now()
        return obj

    mock.refresh = AsyncMock(side_effect=mock_refresh)
    mock.scalar = AsyncMock()
    mock.scalars = AsyncMock()
    
    # Configure mock results
    project_result = MagicMock()
    project_result.scalar_one_or_none = lambda: mock_project
    project_result.unique = lambda: project_result
    project_result.scalars = lambda: MagicMock(all=lambda: [mock_project])
    project_result.scalar_one = lambda: mock_project.active

    version_result = MagicMock()
    version_result.scalar_one_or_none = lambda: mock_version
    version_result.unique = lambda: version_result
    version_result.scalars = lambda: MagicMock(all=lambda: [mock_version])
    version_result.all = lambda: [(mock_version.id, mock_version.version_number, mock_version.name)]

    # Configure execute to return appropriate result
    mock.execute = AsyncMock(return_value=version_result if request.param == "versions" else project_result)
    
    return mock

@pytest.fixture(scope="module")
def client(mock_db):
    """Test client with mocked database."""
    def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter service."""
    with patch('app.services.openrouter.OpenRouterService._get_client') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

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
