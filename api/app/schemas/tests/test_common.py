"""Tests for common schemas."""
import pytest
from pydantic import ValidationError
from ...schemas.common import FileOperation, FileChange, AIResponse

def test_file_operation_enum():
    """Test FileOperation enum values."""
    assert FileOperation.CREATE == "create"
    assert FileOperation.UPDATE == "update"
    assert FileOperation.DELETE == "delete"
    
    # Test enum can be created from string
    assert FileOperation("create") == FileOperation.CREATE
    assert FileOperation("update") == FileOperation.UPDATE
    assert FileOperation("delete") == FileOperation.DELETE

def test_file_change_valid():
    """Test creating valid FileChange objects."""
    # CREATE with content
    create_change = FileChange(
        operation=FileOperation.CREATE,
        path="/path/to/file.txt",
        content="File content"
    )
    assert create_change.operation == FileOperation.CREATE
    assert create_change.path == "/path/to/file.txt"
    assert create_change.content == "File content"
    
    # UPDATE with content
    update_change = FileChange(
        operation=FileOperation.UPDATE,
        path="/path/to/file.txt",
        content="Updated content"
    )
    assert update_change.operation == FileOperation.UPDATE
    assert update_change.path == "/path/to/file.txt"
    assert update_change.content == "Updated content"
    
    # DELETE without content
    delete_change = FileChange(
        operation=FileOperation.DELETE,
        path="/path/to/file.txt"
    )
    assert delete_change.operation == FileOperation.DELETE
    assert delete_change.path == "/path/to/file.txt"
    assert delete_change.content is None

def test_file_change_path_validation():
    """Test path validation in FileChange."""
    # Empty path
    with pytest.raises(ValidationError) as exc_info:
        FileChange(
            operation=FileOperation.CREATE,
            path="",
            content="Content"
        )
    assert "File path cannot be empty" in str(exc_info.value)
    
    # Whitespace-only path
    with pytest.raises(ValidationError) as exc_info:
        FileChange(
            operation=FileOperation.CREATE,
            path="   ",
            content="Content"
        )
    assert "File path cannot be empty" in str(exc_info.value)
    
    # Path with leading/trailing whitespace should be stripped
    change = FileChange(
        operation=FileOperation.CREATE,
        path="  /path/with/spaces.txt  ",
        content="Content"
    )
    assert change.path == "/path/with/spaces.txt"  # Whitespace stripped

def test_file_change_content_validation():
    """Test content validation in FileChange."""
    # Missing content for CREATE
    with pytest.raises(ValidationError) as exc_info:
        FileChange(
            operation=FileOperation.CREATE,
            path="/file.txt",
            content=None
        )
    assert "Content required for FileOperation.CREATE operation" in str(exc_info.value)
    
    # Empty content for CREATE
    with pytest.raises(ValidationError) as exc_info:
        FileChange(
            operation=FileOperation.CREATE,
            path="/file.txt",
            content=""
        )
    assert "Content required for FileOperation.CREATE operation" in str(exc_info.value)
    
    # Missing content for UPDATE
    with pytest.raises(ValidationError) as exc_info:
        FileChange(
            operation=FileOperation.UPDATE,
            path="/file.txt",
            content=None
        )
    assert "Content required for FileOperation.UPDATE operation" in str(exc_info.value)
    
    # Content can be empty for DELETE
    delete_change = FileChange(
        operation=FileOperation.DELETE,
        path="/file.txt"
    )
    assert delete_change.content is None
    
    # Content can also be provided for DELETE (but it's ignored)
    delete_with_content = FileChange(
        operation=FileOperation.DELETE,
        path="/file.txt",
        content="This content will be ignored"
    )
    assert delete_with_content.content == "This content will be ignored"

def test_ai_response_valid():
    """Test creating valid AIResponse objects."""
    changes = [
        FileChange(
            operation=FileOperation.CREATE,
            path="/new/file.txt",
            content="New content"
        ),
        FileChange(
            operation=FileOperation.UPDATE,
            path="/existing/file.txt",
            content="Updated content"
        ),
        FileChange(
            operation=FileOperation.DELETE,
            path="/delete/file.txt"
        )
    ]
    
    response = AIResponse(changes=changes)
    assert len(response.changes) == 3
    assert response.changes[0].operation == FileOperation.CREATE
    assert response.changes[1].operation == FileOperation.UPDATE
    assert response.changes[2].operation == FileOperation.DELETE

def test_ai_response_empty_changes():
    """Test AIResponse with empty changes list."""
    response = AIResponse(changes=[])
    assert len(response.changes) == 0

def test_ai_response_missing_changes():
    """Test AIResponse validation for missing changes."""
    with pytest.raises(ValidationError) as exc_info:
        AIResponse()
    assert "Field required" in str(exc_info.value)
    assert "changes" in str(exc_info.value)