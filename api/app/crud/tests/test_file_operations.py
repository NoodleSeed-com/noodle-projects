"""Tests for file operations in version CRUD."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from ...schemas.common import FileChange, FileOperation
from ...models.file import File
from ..version.file_operations import validate_file_changes, apply_file_changes

@pytest.mark.asyncio
async def test_validate_file_changes_valid():
    """Test validation of valid file changes."""
    # Setup existing files
    existing_files = {
        "src/App.tsx": File(
            id=uuid4(),
            version_id=uuid4(),
            path="src/App.tsx",
            content="Original App content"
        ),
        "src/components/HelloWorld.tsx": File(
            id=uuid4(),
            version_id=uuid4(),
            path="src/components/HelloWorld.tsx",
            content="Original HelloWorld content"
        )
    }
    
    # Valid changes
    changes = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/components/NewComponent.tsx",
            content="New component content"
        ),
        FileChange(
            operation=FileOperation.UPDATE,
            path="src/App.tsx",
            content="Updated App content"
        ),
        FileChange(
            operation=FileOperation.DELETE,
            path="src/components/HelloWorld.tsx"
        )
    ]
    
    # Should not raise any exceptions
    await validate_file_changes(changes, existing_files)

@pytest.mark.asyncio
async def test_validate_file_changes_empty_path():
    """Test validation rejects empty file paths."""
    existing_files = {}
    
    # Empty path
    # We'll skip this test since Pydantic validation prevents creating a FileChange with empty path
    # Instead, we'll test the validation directly in the file_operations.py function
    # by mocking the validation
    
    # Create a mock FileChange object
    change = MagicMock(spec=FileChange)
    change.path = "  "  # Whitespace-only path
    change.operation = FileOperation.CREATE
    change.content = "Some content"
    
    changes = [change]
    with pytest.raises(ValueError, match="File path cannot be empty"):
        await validate_file_changes(changes, existing_files)

@pytest.mark.asyncio
async def test_validate_file_changes_missing_content():
    """Test validation rejects missing content for CREATE/UPDATE operations."""
    existing_files = {
        "src/App.tsx": File(
            id=uuid4(),
            version_id=uuid4(),
            path="src/App.tsx",
            content="Original content"
        )
    }
    
    # We'll skip this test since Pydantic validation prevents creating a FileChange with empty content
    # Instead, we'll test the validation directly in the file_operations.py function
    # by mocking the validation
    
    # Create a mock FileChange object for CREATE
    change_create = MagicMock(spec=FileChange)
    change_create.path = "src/components/NewComponent.tsx"
    change_create.operation = FileOperation.CREATE
    change_create.content = ""  # Empty content
    
    changes = [change_create]
    with pytest.raises(ValueError, match=f"Content required for"):
        await validate_file_changes(changes, existing_files)
    
    # Create a mock FileChange object for UPDATE
    change_update = MagicMock(spec=FileChange)
    change_update.path = "src/App.tsx"
    change_update.operation = FileOperation.UPDATE
    change_update.content = ""  # Empty content
    
    changes = [change_update]
    with pytest.raises(ValueError, match=f"Content required for"):
        await validate_file_changes(changes, existing_files)

@pytest.mark.asyncio
async def test_validate_file_changes_duplicate_paths():
    """Test validation rejects duplicate file paths in changes."""
    existing_files = {}
    
    # Duplicate paths
    changes = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/components/NewComponent.tsx",
            content="Content 1"
        ),
        FileChange(
            operation=FileOperation.CREATE,
            path="src/components/NewComponent.tsx",  # Duplicate path
            content="Content 2"
        )
    ]
    
    with pytest.raises(ValueError, match="Duplicate file path in changes"):
        await validate_file_changes(changes, existing_files)

@pytest.mark.asyncio
async def test_validate_file_changes_create_existing():
    """Test validation rejects creating a file that already exists."""
    existing_files = {
        "src/App.tsx": File(
            id=uuid4(),
            version_id=uuid4(),
            path="src/App.tsx",
            content="Original content"
        )
    }
    
    # Try to create existing file
    changes = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/App.tsx",  # Already exists
            content="New content"
        )
    ]
    
    with pytest.raises(ValueError, match="Cannot create file that already exists"):
        await validate_file_changes(changes, existing_files)

@pytest.mark.asyncio
async def test_validate_file_changes_update_nonexistent():
    """Test validation rejects updating a file that doesn't exist."""
    existing_files = {}
    
    # Try to update non-existent file
    changes = [
        FileChange(
            operation=FileOperation.UPDATE,
            path="src/App.tsx",  # Doesn't exist
            content="Updated content"
        )
    ]
    
    with pytest.raises(ValueError, match="Cannot update non-existent file"):
        await validate_file_changes(changes, existing_files)

@pytest.mark.asyncio
async def test_validate_file_changes_delete_nonexistent():
    """Test validation rejects deleting a file that doesn't exist."""
    existing_files = {}
    
    # Try to delete non-existent file
    changes = [
        FileChange(
            operation=FileOperation.DELETE,
            path="src/App.tsx"  # Doesn't exist
        )
    ]
    
    with pytest.raises(ValueError, match="Cannot delete non-existent file"):
        await validate_file_changes(changes, existing_files)

@pytest.mark.asyncio
async def test_apply_file_changes_create(mock_files):
    """Test applying CREATE file changes."""
    # Setup
    new_version_id = uuid4()
    existing_files = {file.path: file for file in mock_files}
    
    # Create a new file
    changes = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/components/NewComponent.tsx",
            content="New component content"
        )
    ]
    
    # Apply changes
    result = await apply_file_changes(new_version_id, changes, existing_files)
    
    # Verify results
    assert len(result) == len(mock_files) + 1  # All existing files + 1 new file
    
    # Find the new file
    new_file = next((f for f in result if f.path == "src/components/NewComponent.tsx"), None)
    assert new_file is not None
    assert new_file.version_id == new_version_id
    assert new_file.content == "New component content"

@pytest.mark.asyncio
async def test_apply_file_changes_update(mock_files):
    """Test applying UPDATE file changes."""
    # Setup
    new_version_id = uuid4()
    existing_files = {file.path: file for file in mock_files}
    
    # Update an existing file
    changes = [
        FileChange(
            operation=FileOperation.UPDATE,
            path="src/App.tsx",
            content="Updated App content"
        )
    ]
    
    # Apply changes
    result = await apply_file_changes(new_version_id, changes, existing_files)
    
    # Verify results
    assert len(result) == len(mock_files)  # Same number of files
    
    # Find the updated file
    updated_file = next((f for f in result if f.path == "src/App.tsx"), None)
    assert updated_file is not None
    assert updated_file.version_id == new_version_id
    assert updated_file.content == "Updated App content"

@pytest.mark.asyncio
async def test_apply_file_changes_delete(mock_files):
    """Test applying DELETE file changes."""
    # Setup
    new_version_id = uuid4()
    existing_files = {file.path: file for file in mock_files}
    
    # Delete an existing file
    changes = [
        FileChange(
            operation=FileOperation.DELETE,
            path="src/components/HelloWorld.tsx"
        )
    ]
    
    # Apply changes
    result = await apply_file_changes(new_version_id, changes, existing_files)
    
    # Verify results
    assert len(result) == len(mock_files) - 1  # One less file
    
    # Verify the file was deleted
    deleted_file = next((f for f in result if f.path == "src/components/HelloWorld.tsx"), None)
    assert deleted_file is None

@pytest.mark.asyncio
async def test_apply_file_changes_multiple_operations(mock_files):
    """Test applying multiple file operations at once."""
    # Setup
    new_version_id = uuid4()
    existing_files = {file.path: file for file in mock_files}
    
    # Multiple operations
    changes = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/components/NewComponent.tsx",
            content="New component content"
        ),
        FileChange(
            operation=FileOperation.UPDATE,
            path="src/App.tsx",
            content="Updated App content"
        ),
        FileChange(
            operation=FileOperation.DELETE,
            path="src/components/HelloWorld.tsx"
        )
    ]
    
    # Apply changes
    result = await apply_file_changes(new_version_id, changes, existing_files)
    
    # Verify results
    assert len(result) == len(mock_files)  # +1 for create, -1 for delete
    
    # Verify created file
    new_file = next((f for f in result if f.path == "src/components/NewComponent.tsx"), None)
    assert new_file is not None
    assert new_file.version_id == new_version_id
    assert new_file.content == "New component content"
    
    # Verify updated file
    updated_file = next((f for f in result if f.path == "src/App.tsx"), None)
    assert updated_file is not None
    assert updated_file.version_id == new_version_id
    assert updated_file.content == "Updated App content"
    
    # Verify deleted file
    deleted_file = next((f for f in result if f.path == "src/components/HelloWorld.tsx"), None)
    assert deleted_file is None
