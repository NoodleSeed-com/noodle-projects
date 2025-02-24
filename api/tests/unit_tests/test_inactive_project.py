"""Unit tests for inactive project operations using mocked OpenRouter service."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.project import (
    FileOperation,
    FileChange,
    ProjectResponse,
    ProjectVersionResponse
)

@pytest.fixture
def project_with_version(mock_db: Session, client: TestClient, mock_openrouter) -> tuple[dict, dict]:
    """Fixture that creates and returns a project with a version."""
    # Create project
    project = client.post("/api/projects/", json={
        "name": "Project with Version",
        "description": "Test Description"
    }).json()

    # Create version
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/Feature.tsx",
            content="export const Feature = () => <div>Feature</div>"
        )
    ]
    version_response = client.post(
        f"/api/projects/{project['id']}/versions",
        json={
            "name": "Test Version",
            "parent_version_number": 0,
            "project_context": "Adding feature",
            "change_request": "Create feature"
        }
    )
    assert version_response.status_code == 200
    return project, version_response.json()

def test_inactive_project_operations(mock_db: Session, client: TestClient, mock_openrouter):
    """Test operations on inactive projects."""
    # Create and deactivate a project
    project = client.post("/api/projects/", json={
        "name": "Inactive Project",
        "description": "Test Description"
    }).json()
    
    delete_response = client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 200
    inactive_project = delete_response.json()
    """Test operations on inactive projects.
    
    Verifies:
    1. Cannot create new versions on inactive project
    2. Cannot modify inactive project
    3. Cannot perform any write operations
    4. Proper error responses returned with correct structure
    """
    project_id = inactive_project["id"]

    # Test all write operations
    operations = [
        # Attempt to create version
        ("POST", f"/api/projects/{project_id}/versions", {
            "name": "New Feature",
            "parent_version_number": 0,
            "project_context": "Adding feature to inactive project",
            "change_request": "Create feature"
        }),
        # Attempt to modify project
        ("PUT", f"/api/projects/{project_id}", {
            "name": "New Name",
            "description": "New description"
        })
    ]

    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/Feature.tsx",
            content="export const Feature = () => <div>Feature</div>"
        )
    ]

    # Verify all operations fail with proper error structure
    for method, url, data in operations:
        response = client.request(method, url, json=data)
        assert response.status_code == 403
        error = response.json()
        assert "detail" in error
        assert "inactive" in error["detail"].lower()
        assert isinstance(error["detail"], str)

def test_inactive_project_version_operations(project_with_version: tuple[dict, dict], client: TestClient, mock_openrouter):
    """Test operations on versions of inactive projects.
    
    Verifies:
    1. Cannot create new versions from inactive project versions
    2. Read operations still work but show inactive state
    3. Error responses have correct structure
    """
    project, version = project_with_version
    project_id = project["id"]
    version_number = version["version_number"]

    # Soft delete project
    client.delete(f"/api/projects/{project_id}")

    # Attempt to create new version from inactive project's version
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/NewFeature.tsx",
            content="export const NewFeature = () => <div>New Feature</div>"
        )
    ]
    
    response = client.post(
        f"/api/projects/{project_id}/versions",
        json={
            "name": "New Feature",
            "parent_version_number": version_number,
            "project_context": "Adding feature to inactive project",
            "change_request": "Create feature"
        }
    )
    assert response.status_code == 403
    error = response.json()
    assert "detail" in error
    assert "inactive" in error["detail"].lower()
    assert isinstance(error["detail"], str)

    # Verify read operations work but show inactive state
    version_response = client.get(f"/api/projects/{project_id}/versions/{version_number}")
    assert version_response.status_code == 200
    version_data = version_response.json()
    version = ProjectVersionResponse(**version_data)
    assert version.active is False
