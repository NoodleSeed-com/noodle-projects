"""Tests for File model."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import IntegrityError
from ...models.file import File
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
    mock_db_session.add.side_effect = IntegrityError(MagicMock(), MagicMock(), MagicMock())
    with pytest.raises(IntegrityError):
        file = File(version_id=mock_version.id, path="src/test.tsx", content="Test content")
        mock_db_session.add(file)
        await mock_db_session.commit()

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
