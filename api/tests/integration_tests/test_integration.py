"""
Integration tests for project deletion functionality.
Tests follow FastAPI best practices and ensure proper soft deletion behavior.
"""
import pytest
import pytest_asyncio
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pydantic import ValidationError, TypeAdapter
from typing import List
from app.crud import projects
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.models.version import VersionResponse, VersionListItem
from app.models.file import FileOperation, FileChange

# Type adapters for common validations
project_list_adapter = TypeAdapter(List[ProjectResponse])
version_list_adapter = TypeAdapter(List[VersionListItem])

@pytest_asyncio.fixture
async def active_project(db_session, async_client) -> dict:
    """Fixture that creates and returns an active project."""
    response = await async_client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Test Description"
    })
    assert response.status_code == 201
    return response.json()

@pytest_asyncio.fixture
async def inactive_project(db_session, async_client) -> dict:
    """Fixture that creates and returns an inactive project."""
    project_response = await async_client.post("/api/projects/", json={
        "name": "Inactive Project",
        "description": "Test Description"
    })
    project = project_response.json()
    
    delete_response = await async_client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 200
    return delete_response.json()

@pytest.mark.asyncio
async def test_soft_delete_via_api(active_project: dict, async_client):
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
    list_response = await async_client.get("/api/projects/")
    assert list_response.status_code == 200
    projects_list = list_response.json()
    assert any(p["id"] == project_id for p in projects_list)
    
    # Verify list response matches schema
    project_list = project_list_adapter.validate_python(projects_list)
    assert len(project_list) > 0

    # Perform soft delete
    delete_response = await async_client.delete(f"/api/projects/{project_id}")
    assert delete_response.status_code == 200
    deleted_project = delete_response.json()
    
    # Verify response matches schema
    project_response = ProjectResponse(**deleted_project)
    assert str(project_response.id) == project_id
    assert project_response.active is False

    # Verify project not in active projects list
    list_after = await async_client.get("/api/projects/")
    assert list_after.status_code == 200
    assert not any(p["id"] == project_id for p in list_after.json())

    # Verify project still accessible directly
    get_response = await async_client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    project = get_response.json()
    
    # Verify response matches schema
    project_response = ProjectResponse(**project)
    assert str(project_response.id) == project_id
    assert project_response.active is False
    assert project_response.name == active_project["name"]
    assert project_response.description == active_project["description"]

@pytest.mark.asyncio
async def test_invalid_project_operations(async_client):
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
        ("GET", f"/api/projects/{invalid_id}/versions")
    ]

    for method, url, *data in operations:
        response = await async_client.request(method, url, json=data[0] if data else None)
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
        # FastAPI validation error returns details as a string representation of list in the test environment
        # Check for UUID validation mention in the error
        assert "uuid" in str(error["detail"]).lower()

    # Test non-existent but valid UUID
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    operations = [
        ("GET", f"/api/projects/{fake_id}"),
        ("PUT", f"/api/projects/{fake_id}", {"name": "New Name"}),
        ("DELETE", f"/api/projects/{fake_id}"),
        ("GET", f"/api/projects/{fake_id}/versions")
    ]

    for method, url, *data in operations:
        response = await async_client.request(method, url, json=data[0] if data else None)
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

@pytest.mark.asyncio
async def test_soft_delete_nonexistent_project(async_client):
    """Test attempting to delete non-existent project.
    
    Verifies:
    1. Appropriate error response for non-existent project
    2. 404 status code returned
    3. Error response contains proper structure
    """
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    response = await async_client.delete(f"/api/projects/{fake_id}")
    assert response.status_code == 404
    
    error = response.json()
    assert "detail" in error
    assert "not found" in error["detail"].lower()

@pytest.mark.asyncio
async def test_soft_delete_reactivation(inactive_project: dict, async_client):
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
    list_response = await async_client.get("/api/projects/")
    assert not any(p["id"] == project_id for p in list_response.json())
    
    # Reactivate project
    update_response = await async_client.put(
        f"/api/projects/{project_id}",
        json={"active": True}
    )
    assert update_response.status_code == 200
    updated_project = update_response.json()
    
    # Verify response matches schema
    project_response = ProjectResponse(**updated_project)
    assert project_response.active is True
    
    # Verify appears in active list
    list_after = await async_client.get("/api/projects/")
    assert any(p["id"] == project_id for p in list_after.json())
    
    # Verify all data preserved
    get_response = await async_client.get(f"/api/projects/{project_id}")
    project = get_response.json()
    project_response = ProjectResponse(**project)
    assert project_response.name == inactive_project["name"]
    assert project_response.description == inactive_project["description"]

    # Verify version 0 inherits active state
    version_response = await async_client.get(f"/api/projects/{project_id}/versions/0")
    assert version_response.status_code == 200
    version_data = version_response.json()
    version = VersionResponse(**version_data)
    assert version.active is True
