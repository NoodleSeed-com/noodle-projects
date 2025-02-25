"""Test fixtures for routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
from ...main import app
from ...services.openrouter import get_openrouter
from ...config import get_db
from ...models.project import Project
from ...models.version import Version
from ...models.file import File

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
    version_id = uuid4()
    version = Version(
        id=version_id,
        project_id=mock_project.id,
        version_number=0,  # This is correct - initial version is 0
        name="Initial Version",
        parent_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Create file with version_id
    file = File(
        id=uuid4(),
        version_id=version_id,  # Set version_id explicitly
        path="src/test.tsx",
        content="export const Test = () => <div>Test</div>",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Initialize files list
    version.files = [file]
    
    # Set up bidirectional relationships
    file.version = version
    
    # Set up project relationship
    version.project = mock_project
    mock_project.versions = [version]
    
    return version

@pytest.fixture(scope="module")
def mock_db(mock_project, mock_version):
    """Mock database session for testing."""
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
    mock.execute = AsyncMock(return_value=version_result)
    
    return mock

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
def client(mock_db: Session):
    """Test client with mocked database."""
    def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
