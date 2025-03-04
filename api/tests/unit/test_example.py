"""
Example unit test demonstrating best practices.

This file shows how to structure unit tests with proper mocking,
isolation, and validation of edge cases.
"""
import pytest
import pytest_asyncio
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.file import FileChange, FileOperation
from app.crud.version.file_operations import validate_file_changes


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_file_changes_with_valid_input(mock_supabase_client):
    """Test validating file changes with valid input."""
    # Arrange
    existing_files = {
        "src/App.tsx": MagicMock(path="src/App.tsx", content="Original content")
    }
    
    changes = [
        FileChange(
            path="src/components/NewComponent.tsx",
            content="export const NewComponent = () => <div>New</div>;",
            operation=FileOperation.CREATE
        ),
        FileChange(
            path="src/App.tsx",
            content="export const App = () => <div>Updated</div>;",
            operation=FileOperation.UPDATE
        )
    ]
    
    # Act & Assert - Should not raise any exceptions
    await validate_file_changes(changes, existing_files)
    

@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_file_changes_with_duplicate_paths(mock_supabase_client):
    """Test validating file changes with duplicate paths."""
    # Arrange
    existing_files = {}
    
    changes = [
        FileChange(
            path="src/components/Component.tsx",
            content="Content 1",
            operation=FileOperation.CREATE
        ),
        FileChange(
            path="src/components/Component.tsx",  # Duplicate path
            content="Content 2",
            operation=FileOperation.CREATE
        )
    ]
    
    # Act & Assert - Should raise ValueError with specific message
    with pytest.raises(ValueError, match="Duplicate file path in changes"):
        await validate_file_changes(changes, existing_files)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_file_changes_create_existing_file(mock_supabase_client):
    """Test validating file changes trying to create an existing file."""
    # Arrange
    existing_files = {
        "src/App.tsx": MagicMock(path="src/App.tsx", content="Original content")
    }
    
    changes = [
        FileChange(
            path="src/App.tsx",  # Already exists
            content="New content",
            operation=FileOperation.CREATE
        )
    ]
    
    # Act & Assert - Should raise ValueError
    with pytest.raises(ValueError, match="Cannot create file that already exists"):
        await validate_file_changes(changes, existing_files)


@pytest.mark.parametrize("operation,exists,error_expected,error_message", [
    (FileOperation.CREATE, False, False, None),              # Create new file - valid
    (FileOperation.CREATE, True, True, "Cannot create file that already exists"),  # Create existing - invalid
    (FileOperation.UPDATE, True, False, None),               # Update existing - valid
    (FileOperation.UPDATE, False, True, "Cannot update non-existent file"),  # Update non-existent - invalid
    (FileOperation.DELETE, True, False, None),               # Delete existing - valid
    (FileOperation.DELETE, False, True, "Cannot delete non-existent file")   # Delete non-existent - invalid
])
@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_file_changes_operation_rules(
    mock_supabase_client, operation, exists, error_expected, error_message
):
    """Test validating file changes with different operation rules using parameterization."""
    # Arrange
    test_path = "src/test.tsx"
    existing_files = {}
    
    if exists:
        existing_files[test_path] = MagicMock(path=test_path, content="Original content")
    
    changes = [
        FileChange(
            path=test_path,
            content="Test content" if operation != FileOperation.DELETE else None,
            operation=operation
        )
    ]
    
    # Act & Assert
    if error_expected:
        with pytest.raises(ValueError, match=error_message):
            await validate_file_changes(changes, existing_files)
    else:
        # Should not raise exceptions
        await validate_file_changes(changes, existing_files)