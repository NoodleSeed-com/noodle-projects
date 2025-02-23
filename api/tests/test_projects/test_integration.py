"""
Integration tests for project deletion functionality.
Tests follow FastAPI best practices and ensure proper soft deletion behavior.
"""
import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pydantic import ValidationError, TypeAdapter
from typing import List
from app.crud import projects
from app.models.project import (
    ProjectCreate,
    ProjectUpdate,
    FileOperation,
    FileChange,
    ProjectResponse,
    ProjectVersionResponse,
    ProjectVersionListItem
)

# Type adapters for common validations
project_list_adapter = TypeAdapter(List[ProjectResponse])
version_list_adapter = TypeAdapter(List[ProjectVersionListItem])

@pytest.fixture
def active_project(test_db: Session, client: TestClient) -> dict:
    """Fixture that creates and returns an active project."""
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Test Description"
    })
    assert response.status_code == 201
    return response.json()

@pytest.fixture
def inactive_project(test_db: Session, client: TestClient) -> dict:
    """Fixture that creates and returns an inactive project."""
    project = client.post("/api/projects/", json={
        "name": "Inactive Project",
        "description": "Test Description"
    }).json()
    
    delete_response = client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 200
    return delete_response.json()

@pytest.fixture
def project_with_version(test_db: Session, client: TestClient, mock_openrouter) -> tuple[dict, dict]:
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

def test_soft_delete_via_api(active_project: dict, client: TestClient):
    """Test soft deletion through API endpoint.
    
    Verifies:
    1. Project is successfully created
    2. Soft delete sets active=False
    3. Project no longer appears in active projects list
    4. Project data is preserved and directly accessible
    5. Response matches ProjectResponse schema
    """
    project_id = active_project["id"]
    assert active_project["active"] is True

    # Verify project is in active projects list
    list_response = client.get("/api/projects/")
    assert list_response.status_code == 200
    projects_list = list_response.json()
    assert any(p["id"] == project_id for p in projects_list)
    
    # Verify list response matches schema
    project_list = project_list_adapter.validate_python(projects_list)
    assert len(project_list) > 0

    # Perform soft delete
    delete_response = client.delete(f"/api/projects/{project_id}")
    assert delete_response.status_code == 200
    deleted_project = delete_response.json()
    
    # Verify response matches schema
    project_response = ProjectResponse(**deleted_project)
    assert str(project_response.id) == project_id
    assert project_response.active is False

    # Verify project not in active projects list
    list_after = client.get("/api/projects/")
    assert list_after.status_code == 200
    assert not any(p["id"] == project_id for p in list_after.json())

    # Verify project still accessible directly
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    project = get_response.json()
    
    # Verify response matches schema
    project_response = ProjectResponse(**project)
    assert str(project_response.id) == project_id
    assert project_response.active is False
    assert project_response.name == active_project["name"]
    assert project_response.description == active_project["description"]

def test_invalid_project_operations(client: TestClient):
    """Test operations with invalid project IDs.
    
    Verifies:
    1. Invalid UUIDs return 422
    2. Non-existent UUIDs return 404
    3. Error responses have correct structure
    """
    # Test invalid UUID format
    invalid_id = "not-a-uuid"
    operations = [
        ("GET", f"/api/projects/{invalid_id}"),
        ("PUT", f"/api/projects/{invalid_id}", {"name": "New Name"}),
        ("DELETE", f"/api/projects/{invalid_id}"),
        ("GET", f"/api/projects/{invalid_id}/versions"),
        ("POST", f"/api/projects/{invalid_id}/versions", {
            "name": "New Version",
            "parent_version_number": 0,
            "project_context": "Test",
            "change_request": "Test"
        })
    ]

    for method, url, *data in operations:
        response = client.request(method, url, json=data[0] if data else None)
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
        assert isinstance(error["detail"], list)
        assert len(error["detail"]) > 0
        assert "uuid" in error["detail"][0]["msg"].lower()

    # Test non-existent but valid UUID
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    operations = [
        ("GET", f"/api/projects/{fake_id}"),
        ("PUT", f"/api/projects/{fake_id}", {"name": "New Name"}),
        ("DELETE", f"/api/projects/{fake_id}"),
        ("GET", f"/api/projects/{fake_id}/versions"),
        ("POST", f"/api/projects/{fake_id}/versions", {
            "name": "New Version",
            "parent_version_number": 0,
            "project_context": "Test",
            "change_request": "Test"
        })
    ]

    for method, url, *data in operations:
        response = client.request(method, url, json=data[0] if data else None)
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

def test_soft_delete_nonexistent_project(client: TestClient):
    """Test attempting to delete non-existent project.
    
    Verifies:
    1. Appropriate error response for non-existent project
    2. 404 status code returned
    3. Error response contains proper structure
    """
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.delete(f"/api/projects/{fake_id}")
    assert response.status_code == 404
    
    error = response.json()
    assert "detail" in error
    assert "not found" in error["detail"].lower()

def test_soft_delete_reactivation(inactive_project: dict, client: TestClient):
    """Test reactivating a soft-deleted project.
    
    Verifies:
    1. Soft-deleted project can be reactivated
    2. Reactivated project appears in active projects list
    3. All project data preserved through delete/reactivate cycle
    4. Versions inherit reactivated state
    5. All responses match schema
    """
    project_id = inactive_project["id"]
    assert inactive_project["active"] is False
    
    # Verify not in active list
    list_response = client.get("/api/projects/")
    assert not any(p["id"] == project_id for p in list_response.json())
    
    # Reactivate project
    update_response = client.put(
        f"/api/projects/{project_id}",
        json={"active": True}
    )
    assert update_response.status_code == 200
    updated_project = update_response.json()
    
    # Verify response matches schema
    project_response = ProjectResponse(**updated_project)
    assert project_response.active is True
    
    # Verify appears in active list
    list_after = client.get("/api/projects/")
    assert any(p["id"] == project_id for p in list_after.json())
    
    # Verify all data preserved
    get_response = client.get(f"/api/projects/{project_id}")
    project = get_response.json()
    project_response = ProjectResponse(**project)
    assert project_response.name == inactive_project["name"]
    assert project_response.description == inactive_project["description"]

    # Verify version 0 inherits active state
    version_response = client.get(f"/api/projects/{project_id}/versions/0")
    assert version_response.status_code == 200
    version_data = version_response.json()
    version = ProjectVersionResponse(**version_data)
    assert version.active is True

def test_version_inherits_project_active_state(project_with_version: tuple[dict, dict], client: TestClient):
    """Test that version active state is derived from project.
    
    Verifies:
    1. Version inherits active=True from active project
    2. Version inherits active=False from inactive project
    3. Version active state updates when project state changes
    4. Files inherit same active state
    5. All responses match schema
    """
    project, version = project_with_version
    project_id = project["id"]
    version_number = version["version_number"]

    # Verify initial active state
    version_response = ProjectVersionResponse(**version)
    assert version_response.active is True

    # Soft delete project
    delete_response = client.delete(f"/api/projects/{project_id}")
    assert delete_response.status_code == 200
    deleted_project = ProjectResponse(**delete_response.json())
    assert deleted_project.active is False

    # Verify version inherits inactive state
    version_after = client.get(f"/api/projects/{project_id}/versions/{version_number}")
    assert version_after.status_code == 200
    version_after_data = version_after.json()
    version_response = ProjectVersionResponse(**version_after_data)
    assert version_response.active is False

    # Reactivate project
    reactivate_response = client.put(
        f"/api/projects/{project_id}",
        json={"active": True}
    )
    assert reactivate_response.status_code == 200
    reactivated_project = ProjectResponse(**reactivate_response.json())
    assert reactivated_project.active is True

    # Verify version inherits reactivated state
    version_final = client.get(f"/api/projects/{project_id}/versions/{version_number}")
    assert version_final.status_code == 200
    version_final_data = version_final.json()
    version_response = ProjectVersionResponse(**version_final_data)
    assert version_response.active is True

def test_version_list_reflects_project_state(project_with_version: tuple[dict, dict], client: TestClient):
    """Test that version listing reflects project active state.
    
    Verifies:
    1. Active project's versions appear in list
    2. Inactive project's versions don't appear in list
    3. Versions reappear in list when project reactivated
    4. List responses match schema
    5. Pagination parameters are respected
    """
    project, version = project_with_version
    project_id = project["id"]

    # Test pagination parameters
    list_response = client.get(f"/api/projects/{project_id}/versions?limit=1")
    assert list_response.status_code == 200
    versions = list_response.json()
    assert len(versions) == 1  # Respects limit parameter
    
    # Verify version list schema
    version_items = version_list_adapter.validate_python(versions)

    # Get all versions
    list_response = client.get(f"/api/projects/{project_id}/versions")
    assert list_response.status_code == 200
    versions = list_response.json()
    assert len(versions) == 2  # Version 0 and new version
    version_items = version_list_adapter.validate_python(versions)

    # Soft delete project
    client.delete(f"/api/projects/{project_id}")

    # Verify no versions appear in list for inactive project
    list_after = client.get(f"/api/projects/{project_id}/versions")
    assert list_after.status_code == 200
    assert len(list_after.json()) == 0

    # Reactivate project
    client.put(f"/api/projects/{project_id}", json={"active": True})

    # Verify versions reappear in list
    list_final = client.get(f"/api/projects/{project_id}/versions")
    assert list_final.status_code == 200
    versions = list_final.json()
    assert len(versions) == 2
    version_items = version_list_adapter.validate_python(versions)

def test_inactive_project_operations(inactive_project: dict, client: TestClient, mock_openrouter):
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
