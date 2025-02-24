"""Tests for Version model."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from ...errors import NoodleError, ErrorType
from datetime import datetime

@pytest.mark.asyncio
async def test_version_creation(mock_db_session, mock_models):
    """Test basic version creation."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.active = True
    mock_project.versions = [MagicMock(spec=Version)]
    mock_project.versions[0].id = uuid4()
    mock_project.versions[0].version_number = 0

    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_version.name = "Test Version"
    mock_version.version_number = 1
    mock_version.active = mock_project.active
    mock_version.created_at = MagicMock()
    mock_version.updated_at = MagicMock()
    mock_version.parent_id = mock_project.versions[0].id

    mock_models.Project.return_value = mock_project
    mock_models.Version.return_value = mock_version
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    version = mock_models.Version(
        project_id=mock_project.id,
        version_number=1,
        name="Test Version",
        parent_id=mock_project.versions[0].id
    )
    mock_db_session.add(version)
    await mock_db_session.commit()
    await mock_db_session.refresh(version)

    assert version.id is not None
    assert version.name == "Test Version"
    assert version.version_number == 1
    assert version.active == mock_project.active
    assert version.created_at is not None
    assert version.updated_at is not None
    assert version.parent_id == mock_project.versions[0].id

@pytest.mark.asyncio
async def test_version_file_relationships(mock_db_session, mock_models):
    """Test version file relationships."""
    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_version.files = []

    mock_models.Version.return_value = mock_version
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    version = Version(project_id=uuid4(), version_number=1, name="Test Version", parent_id=uuid4())
    mock_db_session.add(version)
    await mock_db_session.commit()
    await mock_db_session.refresh(version)

    for i in range(3):
        file = File(
            version_id=version.id,
            path=f"src/test{i}.tsx",
            content=f"Test content {i}"
        )
        version.files.append(file)
        mock_db_session.add(file)
    await mock_db_session.commit()

    assert len(version.files) == 3
    for i, file in enumerate(version.files):
        assert file.path == f"src/test{i}.tsx"
        assert file.content == f"Test content {i}"

    mock_db_session.delete.return_value = None
    mock_db_session.query.return_value.filter.return_value.all.return_value = []

    mock_db_session.delete(version)
    await mock_db_session.commit()

    files = mock_db_session.query(File).filter(File.version_id == version.id).all()
    assert len(files) == 0

@pytest.mark.asyncio
async def test_version_file_constraints(mock_db_session, mock_models):
    """Test version file constraints."""
    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()

    mock_models.Version.return_value = mock_version
    mock_db_session.add.return_value = None
    mock_db_session.commit.side_effect = AsyncMock()
    mock_db_session.rollback.return_value = AsyncMock()

    version = Version(project_id=uuid4(), version_number=1, name="Test Version", parent_id=uuid4())
    mock_db_session.add(version)
    await mock_db_session.commit()

    file1 = File(version_id=version.id, path="src/test.tsx", content="Test content")
    mock_db_session.add(file1)
    await mock_db_session.commit()

    # Reset commit side effect for the duplicate file test
    mock_db_session.commit.side_effect = IntegrityError(None, None, None)
    
    with pytest.raises(IntegrityError):
        file2 = File(version_id=version.id, path="src/test.tsx", content="Different content")
        mock_db_session.add(file2)
        await mock_db_session.commit()
    await mock_db_session.rollback()

    # Reset commit side effect
    mock_db_session.commit.side_effect = AsyncMock()

    with pytest.raises(ValueError, match="File path cannot be empty"):
        File(version_id=version.id, path="", content="Test content")

    with pytest.raises(ValueError, match="File content cannot be null"):
        File(version_id=version.id, path="src/test2.tsx", content=None)

@pytest.mark.asyncio
async def test_version_inheritance(mock_db_session, mock_models):
    """Test version inheritance behavior."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version) for _ in range(4)]
    for i, version in enumerate(mock_project.versions):
        version.id = uuid4()
        version.version_number = i
        version.parent_id = mock_project.versions[i-1].id if i > 0 else None
        version.active = True

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_project.versions

    project = Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    versions = mock_db_session.query(Version).filter(Version.project_id == project.id).order_by(Version.version_number).all()

    assert len(versions) == 4
    for i, version in enumerate(versions):
        assert version.version_number == i
        if i > 0:
            assert version.parent_id == versions[i-1].id

    project.active = False
    for version in versions:
        version.active = False
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    for version in versions:
        await mock_db_session.refresh(version)
        assert version.active is False

@pytest.mark.asyncio
async def test_version_validation(mock_db_session, mock_models):
    """Test version validation rules."""
    mock_project1 = MagicMock(spec=Project)
    mock_project1.id = uuid4()
    mock_project1.versions = [MagicMock(spec=Version)]
    mock_project1.versions[0].id = uuid4()
    mock_project1.versions[0].version_number = 0
    mock_project1.active = True

    mock_project2 = MagicMock(spec=Project)
    mock_project2.id = uuid4()
    mock_project2.versions = [MagicMock(spec=Version)]
    mock_project2.versions[0].id = uuid4()

    mock_models.Project.side_effect = [mock_project1, mock_project2]
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.rollback.return_value = AsyncMock()
    
    # Configure session.get to return our mock project
    mock_db_session.get.side_effect = lambda model, id: mock_project1 if id == mock_project1.id else mock_project2

    # Test 1: Missing project_id
    with pytest.raises(NoodleError, match="project_id is required"):
        Version(name="Test Version")

    # Test 2: Duplicate version number
    mock_db_session.commit.side_effect = IntegrityError(None, None, None)
    version = Version(project_id=mock_project1.id, version_number=0, name="Test Version", parent_id=mock_project1.versions[0].id)
    mock_db_session.add(version)
    with pytest.raises(IntegrityError):
        await mock_db_session.commit()
    await mock_db_session.rollback()

    # Test 3: Invalid parent version from different project
    version = Version(project_id=mock_project1.id, name="Test Version", parent_id=mock_project2.versions[0].id)
    mock_db_session.add(version)
    with pytest.raises(IntegrityError):
        await mock_db_session.commit()
    await mock_db_session.rollback()

    # Test 4: Inactive project
    mock_db_session.commit.side_effect = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_project1.active = False
    
    next_version_number = max(v.version_number for v in mock_project1.versions) + 1
    
    # Mock object_session before creating Version instance
    from unittest.mock import patch
    with patch('sqlalchemy.orm.object_session', return_value=mock_db_session):
        # This should raise NoodleError during initialization
        with pytest.raises(NoodleError, match="Cannot create version in inactive project"):
            Version(project_id=mock_project1.id, version_number=next_version_number, name="Test Version", parent_id=mock_project1.versions[0].id)

@pytest.mark.asyncio
async def test_version_timestamps(mock_db_session, mock_models):
    """Test version timestamp behavior."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version)]
    mock_project.versions[0].id = uuid4()

    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    
    # Initial timestamps
    created_at = datetime(2025, 2, 24, 20, 0, 0)
    updated_at = datetime(2025, 2, 24, 20, 0, 0)
    mock_version.created_at = created_at
    mock_version.updated_at = updated_at

    mock_models.Project.return_value = mock_project
    mock_models.Version.return_value = mock_version
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    version = mock_models.Version(project_id=mock_project.id, version_number=1, name="Test Version", parent_id=mock_project.versions[0].id)
    mock_db_session.add(version)
    await mock_db_session.commit()

    assert version.created_at == created_at
    assert version.updated_at == updated_at

    # Update version and set a new updated_at timestamp
    version.name = "Updated Name"
    new_updated_at = datetime(2025, 2, 24, 20, 1, 0)  # 1 minute later
    mock_version.updated_at = new_updated_at
    await mock_db_session.commit()
    await mock_db_session.refresh(version)

    assert version.created_at == created_at
    assert version.updated_at == new_updated_at
    assert version.updated_at > version.created_at
