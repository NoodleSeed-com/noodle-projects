import pytest
from fastapi.testclient import TestClient

@pytest.mark.anyio
async def test_create_project(client, test_project):
    """Test creating a new project."""
    response = await client.post("/api/projects/", json=test_project)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_project["name"]
    assert data["description"] == test_project["description"]
    assert "id" in data
    assert data["latest_version_number"] == 0  # Verify initial version number

@pytest.mark.anyio
async def test_get_project(client, test_project):
    """Test retrieving a project."""
    # First create a project
    create_response = await client.post("/api/projects/", json=test_project)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Then retrieve it
    response = await client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == test_project["name"]
    assert data["description"] == test_project["description"]
    assert data["latest_version_number"] == 0  # Verify initial version number

@pytest.mark.anyio
async def test_list_projects(client, test_project):
    """Test listing all projects."""
    # Create a test project first
    await client.post("/api/projects/", json=test_project)
    
    response = await client.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.anyio
async def test_update_project(client, test_project):
    """Test updating a project."""
    # First create a project
    create_response = await client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Update the project
    updated_data = {
        "name": "Updated Project",
        "description": "Updated description"
    }
    response = await client.put(f"/api/projects/{project_id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == updated_data["name"]
    assert data["description"] == updated_data["description"]

@pytest.mark.anyio
async def test_delete_project(client, test_project):
    """Test deleting a project."""
    # First create a project
    create_response = await client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Delete the project
    response = await client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = await client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["active"] == False

@pytest.mark.anyio
async def test_version_access_deleted_project(client, test_project):
    """Test version access for deleted projects."""
    # Create project
    response = await client.post("/api/projects/", json=test_project)
    project_id = response.json()["id"]
    
    # Delete project
    await client.delete(f"/api/projects/{project_id}")
    
    # Verify version list still accessible but project inactive
    versions_response = await client.get(f"/api/projects/{project_id}/versions")
    assert versions_response.status_code == 200
    
    # Verify project is marked as inactive
    project_response = await client.get(f"/api/projects/{project_id}")
    assert project_response.status_code == 200
    assert project_response.json()["active"] == False
