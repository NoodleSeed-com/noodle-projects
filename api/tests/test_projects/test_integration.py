import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.crud import projects
from app.models.project import ProjectCreate, FileOperation, FileChange

def get_template_files():
    """Helper function to get all files from the template directory."""
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates', 'version-0')
    files = []
    for root, _, filenames in os.walk(template_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, template_dir)
            with open(file_path, 'r') as f:
                content = f.read()
            files.append((relative_path, content))
    return files

def test_project_template_initialization(test_db: Session, client: TestClient):
    """Test the complete flow of project creation and template initialization."""
    """
    Integration test that verifies the complete flow of:
    1. Creating a new project (which should initialize version 0 from template)
    2. Verifying all template files are copied correctly
    3. Ensuring file paths remain relative and structure is preserved
    4. Validating the version 0 response format
    """
    # Create a new project using the API
    project_response = client.post("/api/projects/", json={
        "name": "Test Template Project",
        "description": "Test project for template initialization"
    })
    assert project_response.status_code == 201
    project_data = project_response.json()
    project_id = project_data["id"]

    # Get version 0 using crud directly (like test_versions.py does)
    version_0 = projects.get_version(test_db, project_id, 0)
    assert version_0 is not None
    assert version_0.version_number == 0
    assert version_0.name == "Initial Version"
    assert version_0.parent_version_id is None

    # Get expected files from template
    expected_files = get_template_files()
    
    # Verify all expected files exist with correct content
    assert len(version_0.files) == len(expected_files)
    
    # Create dictionaries for easy comparison
    actual_files = {f.path: f.content for f in version_0.files}
    expected_files_dict = dict(expected_files)
    
    # Compare files
    assert set(actual_files.keys()) == set(expected_files_dict.keys())
    for path, content in expected_files_dict.items():
        assert actual_files[path] == content, f"Content mismatch for {path}"

def test_project_creation_validation(client: TestClient):
    """Test validation rules for project creation."""
    # Test missing required name field
    response = client.post("/api/projects/", json={
        "description": "Test Description"
    })
    assert response.status_code == 422, "Should reject missing name"

    # Test invalid name
    response = client.post("/api/projects/", json={
        "name": "",  # Empty name should be rejected
        "description": "Test Description"
    })
    assert response.status_code == 422, "Should reject empty name"

    # Test valid creation (description is optional with default value)
    response = client.post("/api/projects/", json={
        "name": "Valid Project"
    })
    assert response.status_code == 201, "Should accept valid project"

def test_file_path_validation(test_db: Session, client: TestClient):
    """Test file path validation rules."""
    # Create a project first
    project_response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Test Description"
    })
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Get version 0
    version_0 = projects.get_version(test_db, project_id, 0)
    assert version_0 is not None

    # Verify no empty paths exist
    for file in version_0.files:
        assert len(file.path.strip()) > 0, "Empty file paths should not be allowed"

    # Verify paths are unique within the version
    paths = [file.path for file in version_0.files]
    assert len(paths) == len(set(paths)), "Duplicate file paths found in version"

@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter service for testing."""
    with patch("app.services.openrouter.OpenRouterService") as MockService:
        mock_service = MockService.return_value
        mock_service.get_file_changes.return_value = [
            FileChange(
                operation=FileOperation.CREATE,
                path="src/NewFeature.tsx",
                content="export const NewFeature = () => <div>New Feature</div>"
            )
        ]
        yield mock_service

def test_complete_project_lifecycle(test_db: Session, client: TestClient, mock_openrouter):
    """Test complete project lifecycle including version creation."""
    # Create project
    project_response = client.post("/api/projects/", json={
        "name": "Lifecycle Test Project",
        "description": "Testing complete project lifecycle"
    })
    assert project_response.status_code == 201
    project_data = project_response.json()
    project_id = project_data["id"]

    # Verify version 0 was created
    version_0 = projects.get_version(test_db, project_id, 0)
    assert version_0 is not None
    assert version_0.version_number == 0

    # Create new version
    version_request = {
        "name": "Feature Addition",
        "parent_version_number": 0,
        "project_context": "Adding a new feature component",
        "change_request": "Create a new feature component"
    }
    version_response = client.post(
        f"/api/projects/{project_id}/versions",
        json=version_request
    )
    assert version_response.status_code == 200
    version_data = version_response.json()

    # Verify new version
    assert version_data["version_number"] == 1
    assert version_data["parent_version"] == 0
    assert any(f["path"] == "src/NewFeature.tsx" for f in version_data["files"])

    # Verify OpenRouter was called correctly
    mock_openrouter.get_file_changes.assert_called_once()
    call_args = mock_openrouter.get_file_changes.call_args[1]
    assert call_args["project_context"] == "Adding a new feature component"
    assert call_args["change_request"] == "Create a new feature component"
