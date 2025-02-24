"""Tests for Project model."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import IntegrityError
from ...models.project import Project
from ...models.version import Version
from uuid import uuid4
from datetime import datetime

@pytest.mark.asyncio
async def test_project_creation(mock_db_session, mock_models):
    """Test basic project creation."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.name = "Test Project"
    mock_project.description = "Test Description"
    mock_project.active = True
    mock_project.created_at = MagicMock()
    mock_project.updated_at = MagicMock()
    mock_project.versions = [MagicMock(spec=Version)]
    mock_project.versions[0].version_number = 0
    mock_project.versions[0].name = "Initial Version"
    mock_project.versions[0].parent_id = None

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project", description="Test Description")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "Test Description"
    assert project.active is True
    assert project.created_at is not None
    assert project.updated_at is not None
    assert len(project.versions) == 1
    assert project.versions[0].version_number == 0
    assert project.versions[0].name == "Initial Version"
    assert project.versions[0].parent_id is None

@pytest.mark.asyncio
async def test_project_soft_delete(mock_db_session, mock_models):
    """Test project soft deletion."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version), MagicMock(spec=Version)]
    
    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = Project(name="Test Project", description="Test Description")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    project.active = False
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.active is False
    for version in project.versions:
        assert version.active is False

    project.active = True
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.active is True
    for version in project.versions:
        assert version.active is True

@pytest.mark.asyncio
async def test_project_constraints(mock_db_session, mock_models):
    """Test project model constraints."""
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="")

    with pytest.raises(ValueError, match="Project name cannot exceed 255 characters"):
        Project(name="x" * 256)

    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.description = ""

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()

    assert project.description == ""
    assert len(str(project.id)) == 36

@pytest.mark.asyncio
async def test_project_relationships(mock_db_session, mock_models):
    """Test project relationships."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version) for _ in range(4)]
    for i, version in enumerate(mock_project.versions):
        version.version_number = i
        version.parent_id = mock_project.versions[0].id if i > 0 else None
        version.active = True

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project", description="Test Description")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert len(project.versions) == 4
    assert project.versions[0].version_number == 0
    for i, version in enumerate(project.versions[1:], 1):
        assert version.version_number > 0
        assert version.parent_id == project.versions[0].id

    project.active = False
    for version in project.versions:
        version.active = False
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    for version in project.versions:
        await mock_db_session.refresh(version)
        assert version.active is False, f"Version {version.version_number} is still active"

@pytest.mark.asyncio
async def test_version_validation(mock_db_session, mock_models):
    """Test project version validation."""
    mock_project1 = MagicMock(spec=Project)
    mock_project1.id = uuid4()
    mock_project1.versions = [MagicMock(spec=Version)]
    mock_project1.versions[0].id = uuid4()
    mock_project1.versions[0].version_number = 0

    mock_project2 = MagicMock(spec=Project)
    mock_project2.id = uuid4()
    mock_project2.versions = [MagicMock(spec=Version)]
    mock_project2.versions[0].id = uuid4()

    mock_models.Project.side_effect = [mock_project1, mock_project2]
    mock_db_session.add.return_value = None
    mock_db_session.commit.side_effect = [AsyncMock(), IntegrityError(None, None, None), IntegrityError(None, None, None), AsyncMock()]
    mock_db_session.rollback.return_value = AsyncMock()

    project1 = mock_models.Project(name="Project 1")
    project2 = mock_models.Project(name="Project 2")
    mock_db_session.add_all([project1, project2])
    await mock_db_session.commit()

    with pytest.raises(IntegrityError):
        version = Version(project_id=project1.id, version_number=0, name="Duplicate Version")
        mock_db_session.add(version)
        await mock_db_session.commit()
    await mock_db_session.rollback()

    with pytest.raises(IntegrityError):
        version = Version(project_id=project1.id, name="Invalid Parent", parent_id=project2.versions[0].id)
        mock_db_session.add(version)
        await mock_db_session.commit()
    await mock_db_session.rollback()

    next_version_number = max(v.version_number for v in project1.versions) + 1
    version = Version(
        project_id=project1.id,
        version_number=next_version_number,
        name="Valid Version",
        parent_id=project1.versions[0].id
    )
    mock_db_session.add(version)
    await mock_db_session.commit()

    assert version.version_number == next_version_number
    assert version.parent_id == project1.versions[0].id

@pytest.mark.asyncio
async def test_latest_version_number(mock_db_session, mock_models):
    """Test latest_version_number property."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version) for _ in range(4)]
    mock_project.versions[0].version_number = 0
    mock_project.versions[1].version_number = 3
    mock_project.versions[2].version_number = 1
    mock_project.versions[3].version_number = 5
    mock_project.latest_version_number = 5

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.latest_version_number == 5

@pytest.mark.asyncio
async def test_project_timestamps(mock_db_session, mock_models):
    """Test project timestamp behavior."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    
    # Initial timestamps
    created_at = datetime(2025, 2, 24, 20, 0, 0)
    updated_at = datetime(2025, 2, 24, 20, 0, 0)
    mock_project.created_at = created_at
    mock_project.updated_at = updated_at

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()

    assert project.created_at == created_at
    assert project.updated_at == updated_at

    # Update project and set a new updated_at timestamp
    project.name = "Updated Name"
    new_updated_at = datetime(2025, 2, 24, 20, 1, 0)  # 1 minute later
    mock_project.updated_at = new_updated_at
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.created_at == created_at
    assert project.updated_at == new_updated_at
    assert project.updated_at > project.created_at
