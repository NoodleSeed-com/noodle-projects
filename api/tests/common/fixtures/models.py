"""
Model fixtures for testing.
"""
import pytest
import uuid
from typing import Dict, Any
from datetime import datetime

from app.models.project import Project
from app.models.version import Version
from app.models.file import File

@pytest.fixture
def mock_project() -> Project:
    """Create a mock project."""
    return Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project",
        active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def mock_version(mock_project: Project) -> Version:
    """Create a mock version."""
    return Version(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        version_number=1,
        name="Test Version",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def mock_version_with_parent(mock_project: Project, mock_version: Version) -> Version:
    """Create a mock version with a parent."""
    return Version(
        id=uuid.uuid4(),
        project_id=mock_project.id,
        version_number=2,
        name="Child Version",
        parent_id=mock_version.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def mock_file(mock_version: Version) -> File:
    """Create a mock file."""
    return File(
        id=uuid.uuid4(),
        version_id=mock_version.id,
        path="src/main.js",
        content="console.log('Hello, world!');",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def mock_files(mock_version: Version) -> Dict[str, File]:
    """Create a dictionary of mock files."""
    return {
        "src/main.js": File(
            id=uuid.uuid4(),
            version_id=mock_version.id,
            path="src/main.js",
            content="console.log('Hello, world!');",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        "src/utils.js": File(
            id=uuid.uuid4(),
            version_id=mock_version.id,
            path="src/utils.js",
            content="export function add(a, b) { return a + b; }",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        "README.md": File(
            id=uuid.uuid4(),
            version_id=mock_version.id,
            path="README.md",
            content="# Test Project\n\nThis is a test project.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    }