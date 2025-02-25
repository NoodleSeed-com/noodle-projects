"""Tests for version routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ...schemas.common import FileOperation, FileChange
from ...schemas.project import ProjectCreate
from ...schemas.version import CreateVersionRequest

def test_create_version_with_changes(client: TestClient, mock_openrouter):
    """Test creating a new version with AI-generated changes."""
    # Create initial project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Test Description"
    })
    assert response.status_code == 201
    project = response.json()
    
    # Configure mock response
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/NewComponent.tsx",
            content="export const NewComponent = () => <div>New Component</div>"
        ),
        FileChange(
            operation=FileOperation.UPDATE,
            path="src/App.tsx",
            content="import { NewComponent } from './NewComponent';\n\nexport const App = () => <NewComponent />;"
        ),
        FileChange(
            operation=FileOperation.DELETE,
            path="src/components/HelloWorld.tsx"
        )
    ]
    
    # Create version request
    request = CreateVersionRequest(
        name="Updated Version",
        parent_version_number=0,
        project_context="React project that needs a new component",
        change_request="Add a new component and update App.tsx to use it"
    ).model_dump()
    
    # Make the request
    response = client.post(
        f"/api/projects/{project['id']}/versions",
        json=request
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Version"
    assert data["version_number"] == 1
    assert data["parent_version"] == 0
    
    # Verify file changes
    files = {f["path"]: f for f in data["files"]}
    
    # New file was created
    assert "src/NewComponent.tsx" in files
    assert files["src/NewComponent.tsx"]["content"] == "export const NewComponent = () => <div>New Component</div>"
    
    # Existing file was updated
    assert "src/App.tsx" in files
    assert files["src/App.tsx"]["content"] == "import { NewComponent } from './NewComponent';\n\nexport const App = () => <NewComponent />;"
    
    # File was deleted
    assert "src/components/HelloWorld.tsx" not in files
    
    # Verify OpenRouter service was called correctly
    mock_openrouter.get_file_changes.assert_called_once()
    call_args = mock_openrouter.get_file_changes.call_args[1]  # Get kwargs
    assert call_args["project_context"] == "React project that needs a new component"
    assert call_args["change_request"] == "Add a new component and update App.tsx to use it"
    assert len(call_args["current_files"]) > 0  # Verify files were passed


def test_version_validation(client: TestClient, mock_openrouter):
    """Test version number validation.
    
    Verifies:
    1. Cannot create version with negative number
    2. Cannot create duplicate version numbers
    3. Version 0 is reserved for initial version
    4. Proper error responses
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing version validation"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    
    # Test invalid version numbers
    invalid_versions = [
        # Negative version number
        {
            "name": "Invalid Version",
            "parent_version_number": -1,
            "project_context": "Testing validation",
            "change_request": "Create version"
        },
        # Duplicate version number (0 already exists)
        {
            "name": "Duplicate Version",
            "version_number": 0,
            "parent_version_number": 0,
            "project_context": "Testing validation",
            "change_request": "Create version"
        }
    ]
    
    for version_data in invalid_versions:
        response = client.post(
            f"/api/projects/{project_id}/versions",
            json=version_data
        )
        assert response.status_code in (400, 409)
        error = response.json()
        assert "detail" in error
        assert isinstance(error["detail"], str)

def test_version_file_operations(client: TestClient, mock_openrouter):
    """Test file operations within versions.
    
    Verifies:
    1. Cannot have duplicate file paths in version
    2. File paths must be relative to project root
    3. Empty paths are rejected
    4. Proper error responses
    """
    # Create test project and version
    project = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing file operations"
    }).json()
    
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    
    version_response = client.post(
        f"/api/projects/{project['id']}/versions",
        json={
            "name": "Test Version",
            "parent_version_number": 0,
            "project_context": "Testing files",
            "change_request": "Create version"
        }
    )
    assert version_response.status_code == 200
    version = version_response.json()
    
    # Test invalid file operations
    invalid_files = [
        # Empty path
        {
            "path": "",
            "content": "test content"
        },
        # Duplicate path
        {
            "path": "src/test.tsx",
            "content": "duplicate content"
        },
        # Absolute path
        {
            "path": "/absolute/path/test.tsx",
            "content": "test content"
        }
    ]
    
    for file_data in invalid_files:
        response = client.post(
            f"/api/projects/{project['id']}/versions/{version['version_number']}/files",
            json=file_data
        )
        assert response.status_code in (400, 409)
        error = response.json()
        assert "detail" in error
        assert isinstance(error["detail"], str)
