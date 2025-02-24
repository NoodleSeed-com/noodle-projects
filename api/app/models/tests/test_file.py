"""Tests for File model."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import IntegrityError
from ...models.file import File
from ...models.version import Version
from ...models.project import Project
from datetime import datetime

@pytest.mark.asyncio
async def test_file_creation(mock_db_session, mock_models):
    """Test basic file creation."""
    mock_version = MagicMock(id=uuid4())
    mock_file = MagicMock(spec=File)
    mock_file.id = uuid4()
    mock_file.path = "src/test.tsx"
    mock_file.content = "Test content"
    mock_file.version_id = mock_version.id
    mock_file.created_at = MagicMock()
    mock_file.updated_at = MagicMock()

    mock_models.File.return_value = mock_file
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    file = mock_models.File(
        version_id=mock_version.id,
        path="src/test.tsx",
        content="Test content"
    )
    mock_db_session.add(file)
    await mock_db_session.commit()
    await mock_db_session.refresh(file)

    assert file.id is not None
    assert file.path == "src/test.tsx"
    assert file.content == "Test content"
    assert file.version_id == mock_version.id
    assert file.created_at is not None
    assert file.updated_at is not None

@pytest.mark.asyncio
async def test_file_path_constraints(mock_db_session, mock_models):
    """Test file path constraints."""
    mock_version = MagicMock(id=uuid4())

    # Test empty path
    with pytest.raises(ValueError, match="File path cannot be empty"):
        File(version_id=mock_version.id, path="", content="Test content")

    # Test path too long
    with pytest.raises(ValueError, match="File path cannot exceed 1024 characters"):
        File(version_id=mock_version.id, path="x" * 1025, content="Test content")

    # Test duplicate path in same version
    mock_file = MagicMock(spec=File)
    mock_file.id = uuid4()
    mock_file.path = "src/test.tsx"
    mock_file.content = "Test content"
    mock_file.version_id = mock_version.id

    mock_models.File.return_value = mock_file
    mock_db_session.add.return_value = None
    mock_db_session.commit.side_effect = IntegrityError(None, None, None)
    mock_db_session.rollback.return_value = AsyncMock()

    with pytest.raises(IntegrityError):
        file = mock_models.File(version_id=mock_version.id, path="src/test.tsx", content="Test content")
        mock_db_session.add(file)
        await mock_db_session.commit()
    await mock_db_session.rollback()
    
    # Reset mock for subsequent tests
    mock_db_session.commit.side_effect = None

@pytest.mark.asyncio
async def test_file_content_constraints(mock_db_session, mock_models):
    """Test file content constraints."""
    mock_version = MagicMock(id=uuid4())

    # Test null content
    with pytest.raises(ValueError, match="File content cannot be null"):
        File(version_id=mock_version.id, path="src/test.tsx", content=None)

    # Test empty content
    file = File(version_id=mock_version.id, path="src/test.tsx", content="")
    mock_db_session.add(file)
    await mock_db_session.commit()

    # Test large content
    large_content = "x" * (1024 * 1024)
    file = File(version_id=mock_version.id, path="src/test.tsx", content=large_content)
    mock_db_session.add(file)
    await mock_db_session.commit()
    assert len(file.content) == len(large_content)

@pytest.mark.asyncio
async def test_file_version_relationship(mock_db_session, mock_models):
    """Test file-version relationship."""
    mock_version = MagicMock(id=uuid4())

    # Test missing version_id
    with pytest.raises(ValueError, match="version_id is required"):
        File(path="src/test.tsx", content="Test content")

    # Test non-existent version_id
    mock_db_session.commit.side_effect = IntegrityError(None, None, None)
    with pytest.raises(IntegrityError):
        file = mock_models.File(version_id=uuid4(), path="src/test.tsx", content="Test content")
        mock_db_session.add(file)
        await mock_db_session.commit()
    mock_db_session.commit.side_effect = None

    # Add multiple files and verify ordering
    paths = ["src/c.tsx", "src/a.tsx", "src/b.tsx"]
    mock_version.files = [MagicMock(path=path) for path in paths]
    mock_version.files.sort(key=lambda f: f.path)

    assert len(mock_version.files) == 3
    assert [f.path for f in mock_version.files] == sorted(paths)

    # Test cascade delete behavior
    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_version.files = []

    mock_models.Version.return_value = mock_version
    mock_db_session.add.return_value = None
    mock_db_session.commit.side_effect = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create version with files
    version = mock_models.Version(project_id=uuid4(), version_number=1, name="Test Version")
    mock_db_session.add(version)
    await mock_db_session.commit()

    # Add files to version
    files = []
    for i in range(3):
        file = mock_models.File(
            version_id=version.id,
            path=f"src/test{i}.tsx",
            content=f"Test content {i}"
        )
        files.append(file)
        mock_db_session.add(file)
    await mock_db_session.commit()

    # Mock query results for version's files
    mock_db_session.query.return_value.filter.return_value.all.side_effect = [
        files,  # First call returns files
        []      # Second call after delete returns empty list
    ]

    # Verify files exist
    version_files = mock_db_session.query(File).filter(File.version_id == version.id).all()
    assert len(version_files) == 3

    # Delete version
    mock_db_session.delete(version)
    await mock_db_session.commit()

    # Verify files were cascade deleted
    remaining_files = mock_db_session.query(File).filter(File.version_id == version.id).all()
    assert len(remaining_files) == 0

@pytest.mark.asyncio
async def test_file_version_validation(mock_db_session, mock_models):
    """Test file version validation."""
    # Test file creation without version_id
    with pytest.raises(ValueError, match="version_id is required"):
        File()

    with pytest.raises(ValueError, match="version_id is required"):
        File(path="src/test.tsx", content="Test content")

    # Test file creation with invalid version_id
    mock_db_session.commit.side_effect = IntegrityError(None, None, None)
    with pytest.raises(IntegrityError):
        file = File(version_id=uuid4(), path="src/test.tsx", content="Test content")
        mock_db_session.add(file)
        await mock_db_session.commit()
    await mock_db_session.rollback()

    # Test file creation with valid version_id
    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_db_session.commit.side_effect = None
    mock_db_session.commit.return_value = AsyncMock()

    file = File(version_id=mock_version.id, path="src/test.tsx", content="Test content")
    mock_db_session.add(file)
    await mock_db_session.commit()

    assert file.version_id == mock_version.id

@pytest.mark.asyncio
async def test_file_timestamps(mock_db_session, mock_models):
    """Test file timestamp behavior."""
    mock_version = MagicMock(id=uuid4())
    mock_file = MagicMock(spec=File)
    
    # Initial timestamps
    created_at = datetime(2025, 2, 24, 20, 0, 0)
    updated_at = datetime(2025, 2, 24, 20, 0, 0)
    mock_file.created_at = created_at
    mock_file.updated_at = updated_at

    mock_models.File.return_value = mock_file
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    file = mock_models.File(version_id=mock_version.id, path="src/test.tsx", content="Test content")
    mock_db_session.add(file)
    await mock_db_session.commit()

    assert file.created_at == created_at
    assert file.updated_at == updated_at

    # Update file and set a new updated_at timestamp
    file.content = "Updated content"
    new_updated_at = datetime(2025, 2, 24, 20, 1, 0)  # 1 minute later
    mock_file.updated_at = new_updated_at
    await mock_db_session.commit()
    await mock_db_session.refresh(file)

    assert file.created_at == created_at
    assert file.updated_at == new_updated_at
    assert file.updated_at > file.created_at

@pytest.mark.asyncio
async def test_file_ordering(mock_db_session, mock_models):
    """Test file ordering within a version."""
    mock_version = MagicMock(id=uuid4())
    mock_version.files = []

    # Create files in non-alphabetical order
    paths = ["src/z.tsx", "src/a.tsx", "src/m.tsx"]
    
    for path in paths:
        mock_file = MagicMock(spec=File)
        mock_file.id = uuid4()
        mock_file.path = path
        mock_file.content = f"Content for {path}"
        mock_file.version_id = mock_version.id
        mock_version.files.append(mock_file)

    # Verify files are ordered by path
    mock_version.files.sort(key=lambda f: f.path)
    ordered_paths = [f.path for f in mock_version.files]
    assert ordered_paths == sorted(paths)

@pytest.mark.asyncio
async def test_file_version_timestamps(mock_db_session, mock_models):
    """Test file operations affecting version timestamps."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.active = True

    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_version.project_id = mock_project.id
    mock_version.created_at = datetime(2025, 2, 24, 20, 0, 0)
    mock_version.updated_at = datetime(2025, 2, 24, 20, 0, 0)

    def mock_get(model_class, id_):
        if model_class == Project and id_ == mock_project.id:
            return mock_project
        return None
    mock_db_session.get = MagicMock(side_effect=mock_get)

    mock_models.Version.return_value = mock_version
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create version
    version = mock_models.Version(project_id=mock_project.id, version_number=1)
    mock_db_session.add(version)
    await mock_db_session.commit()
    initial_version_updated_at = version.updated_at

    # Add file should update version timestamp
    mock_file = MagicMock(spec=File)
    mock_file.id = uuid4()
    mock_file.path = "src/test.tsx"
    mock_file.content = "Test content"
    mock_file.version_id = version.id
    mock_version.updated_at = datetime(2025, 2, 24, 20, 1, 0)
    
    file = mock_models.File(version_id=version.id, path="src/test.tsx", content="Test content")
    mock_db_session.add(file)
    await mock_db_session.commit()
    await mock_db_session.refresh(version)
    
    assert version.updated_at > initial_version_updated_at

    # Update file should update version timestamp
    initial_version_updated_at = version.updated_at
    file.content = "Updated content"
    mock_version.updated_at = datetime(2025, 2, 24, 20, 2, 0)
    await mock_db_session.commit()
    await mock_db_session.refresh(version)
    
    assert version.updated_at > initial_version_updated_at

    # Delete file should update version timestamp
    initial_version_updated_at = version.updated_at
    mock_db_session.delete(file)
    mock_version.updated_at = datetime(2025, 2, 24, 20, 3, 0)
    await mock_db_session.commit()
    await mock_db_session.refresh(version)
    
    assert version.updated_at > initial_version_updated_at

@pytest.mark.asyncio
async def test_bulk_file_operations(mock_db_session, mock_models):
    """Test bulk file operations within a version."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.active = True

    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_version.project_id = mock_project.id
    mock_version.files = []

    def mock_get(model_class, id_):
        if model_class == Project and id_ == mock_project.id:
            return mock_project
        return None
    mock_db_session.get = MagicMock(side_effect=mock_get)

    mock_models.Version.return_value = mock_version
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create version
    version = mock_models.Version(project_id=mock_project.id, version_number=1)
    mock_db_session.add(version)
    await mock_db_session.commit()

    # Bulk create files
    files = []
    for i in range(5):
        mock_file = MagicMock(spec=File)
        mock_file.id = uuid4()
        mock_file.path = f"src/test{i}.tsx"
        mock_file.content = f"Test content {i}"
        mock_file.version_id = version.id
        mock_version.files.append(mock_file)
        
        file = mock_models.File(
            version_id=version.id,
            path=f"src/test{i}.tsx",
            content=f"Test content {i}"
        )
        files.append(file)
        mock_db_session.add(file)
    
    await mock_db_session.commit()
    assert len(mock_version.files) == 5

    # Bulk update files
    for file in files:
        file.content = f"Updated content for {file.path}"
    await mock_db_session.commit()

    # Bulk delete files
    for file in files:
        mock_db_session.delete(file)
    await mock_db_session.commit()
    mock_version.files = []
    assert len(mock_version.files) == 0

@pytest.mark.asyncio
async def test_file_operations_inactive_project(mock_db_session, mock_models):
    """Test file operations in inactive projects."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.active = False

    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_version.project_id = mock_project.id
    mock_version.active = False

    def mock_get(model_class, id_):
        if model_class == Project and id_ == mock_project.id:
            return mock_project
        elif model_class == Version and id_ == mock_version.id:
            return mock_version
        return None
    mock_db_session.get = MagicMock(side_effect=mock_get)

    # Test file creation in inactive project
    file = File(version_id=mock_version.id, path="src/test.tsx", content="Test content")
    mock_db_session.add(file)
    
    # Should still allow file operations in inactive projects
    await mock_db_session.commit()
    
    # Update file in inactive project
    file.content = "Updated content"
    await mock_db_session.commit()
    
    # Delete file in inactive project
    mock_db_session.delete(file)
    await mock_db_session.commit()
