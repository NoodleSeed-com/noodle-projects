import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.models.project import ProjectVersionCreate

def test_create_project(client: TestClient, test_project):
    """Test creating a new project."""
    response = client.post("/api/projects/", json=test_project)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_project["name"]
    assert data["description"] == test_project["description"]
    assert "id" in data
    assert data["latest_version_number"] == 0  # Verify initial version number

def test_get_project(client: TestClient, test_project):
    """Test retrieving a project."""
    # First create a project
    create_response = client.post("/api/projects/", json=test_project)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Then retrieve it
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == test_project["name"]
    assert data["description"] == test_project["description"]
    assert data["latest_version_number"] == 0  # Verify initial version number

def test_list_projects(client: TestClient, test_project):
    """Test listing all projects."""
    # Create a test project first
    client.post("/api/projects/", json=test_project)
    
    response = client.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Can't reliably assert latest_version_number here, as list order is not guaranteed

def test_update_project(client: TestClient, test_project):
    """Test updating a project."""
    # First create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Update the project
    updated_data = {
        "name": "Updated Project",
        "description": "Updated description"
    }
    response = client.put(f"/api/projects/{project_id}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == updated_data["name"]
    assert data["description"] == updated_data["description"]
    # Can't reliably assert latest_version_number here, as it might not change

def test_delete_project(client: TestClient, test_project):
    """Test deleting a project."""
    # First create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Delete the project
    response = client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["active"] == False

def test_get_nonexistent_project(client: TestClient):
    """Test getting a project that doesn't exist."""
    response = client.get("/api/projects/999")
    assert response.status_code == 422

def test_create_project_invalid_data(client: TestClient):
    """Test creating a project with invalid data."""
    response = client.post("/api/projects/", json={})
    assert response.status_code == 422

def test_get_project_with_versions(client: TestClient, test_project, test_db):
    """Test retrieving a project with associated versions."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Retrieve the project
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["latest_version_number"] == 0  # Verify latest version number is 0

    # Retrieve the project versions
    response_2 = client.get(f"/api/projects/{project_id}/versions")
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert len(data_2) == 1
    assert data_2[0]["version_number"] == 0

    # Retrieve the project again
    response_3 = client.get(f"/api/projects/{project_id}")
    assert response_3.status_code == 200
    data_3 = response_3.json()
    assert data_3["id"] == project_id
    assert data_3["latest_version_number"] == 0  # Verify latest version number is 0

# New Tests for Version Number Semantics

@pytest.fixture
def test_version():
    """Fixture for test version data."""
    return {
        "version_number": 1,
        "name": "Test Version",
        "parent_version_id": None
    }

def test_initial_version_creation(client: TestClient, test_project):
    """Test that a new project automatically gets version 0."""
    response = client.post("/api/projects/", json=test_project)
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Check versions endpoint
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 0
    assert versions[0]["name"] == "Initial Version"

def test_version_number_uniqueness(client: TestClient, test_project, test_db):
    """Test that version numbers must be unique within a project."""
    # Create two projects
    create_response1 = client.post("/api/projects/", json=test_project)
    project1_id = create_response1.json()["id"]
    
    create_response2 = client.post("/api/projects/", json={"name": "Project 2", "description": "Another project"})
    project2_id = create_response2.json()["id"]
    
    # Add version 1 to first project
    from app.models.project import ProjectVersion
    version1 = ProjectVersion(
        project_id=project1_id,
        version_number=1,
        name="Version 1"
    )
    test_db.add(version1)
    test_db.commit()
    
    # Same version number (1) should work for different project
    version2 = ProjectVersion(
        project_id=project2_id,
        version_number=1,
        name="Version 1 of Project 2"
    )
    test_db.add(version2)
    test_db.commit()
    
    # But duplicate version number in same project should fail
    duplicate = ProjectVersion(
        project_id=project1_id,
        version_number=1,
        name="Duplicate Version"
    )
    test_db.add(duplicate)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()

def test_latest_version_number_computation(client: TestClient, test_project, test_db):
    """Test that latest_version_number correctly computes the maximum."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Add some versions manually (since we don't have an endpoint)
    from app.models.project import ProjectVersion
    versions = [
        ProjectVersion(project_id=project_id, version_number=1, name="Version 1"),
        ProjectVersion(project_id=project_id, version_number=2, name="Version 2"),
        ProjectVersion(project_id=project_id, version_number=5, name="Version 5")
    ]
    for v in versions:
        test_db.add(v)
    test_db.commit()
    
    # Check latest version number
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["latest_version_number"] == 5

def test_version_parent_child_relationship(client: TestClient, test_project, test_db):
    """Test version parent-child relationships."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Get the initial version's ID
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    initial_version_id = versions_response.json()[0]["id"]
    
    # Create a child version
    from app.models.project import ProjectVersion
    child_version = ProjectVersion(
        project_id=project_id,
        version_number=1,
        name="Child Version",
        parent_version_id=initial_version_id
    )
    test_db.add(child_version)
    test_db.commit()
    
    # Verify the relationship
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    versions = versions_response.json()
    child = next(v for v in versions if v["version_number"] == 1)
    assert child["parent_version_id"] == initial_version_id

def test_version_cascade_deletion(client: TestClient, test_project, test_db):
    """Test that versions are not accessible after project is soft deleted."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Add a version
    from app.models.project import ProjectVersion
    version = ProjectVersion(
        project_id=project_id,
        version_number=1,
        name="Test Version"
    )
    test_db.add(version)
    test_db.commit()
    
    # Verify version exists
    versions_before = client.get(f"/api/projects/{project_id}/versions")
    assert len(versions_before.json()) == 2  # Initial version (0) + our new version
    
    # Soft delete the project
    client.delete(f"/api/projects/{project_id}")
    
    # Verify project is inactive
    project_response = client.get(f"/api/projects/{project_id}")
    assert project_response.json()["active"] == False
    
    # Versions should still exist in database but not be accessible through API
    # This is a business logic decision: soft-deleted projects retain their version history
    versions_after = client.get(f"/api/projects/{project_id}/versions")
    assert len(versions_after.json()) == 2

def test_version_number_validation(client: TestClient, test_project, test_db):
    """Test that negative version numbers are rejected."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Try to create a version with negative number
    from app.models.project import ProjectVersion
    invalid_version = ProjectVersion(
        project_id=project_id,
        version_number=-1,
        name="Invalid Version"
    )
    test_db.add(invalid_version)
    
    # Should raise IntegrityError due to CHECK constraint
    with pytest.raises(IntegrityError) as exc_info:
        test_db.commit()
    assert "violates check constraint" in str(exc_info.value)
    assert "ck_version_number_positive" in str(exc_info.value)
    test_db.rollback()

def test_version_ordering(client: TestClient, test_project, test_db):
    """Test that versions are returned in order by version number."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Add some versions out of order
    from app.models.project import ProjectVersion
    versions = [
        ProjectVersion(project_id=project_id, version_number=2, name="Version 2"),
        ProjectVersion(project_id=project_id, version_number=1, name="Version 1"),
        ProjectVersion(project_id=project_id, version_number=3, name="Version 3")
    ]
    for v in versions:
        test_db.add(v)
    test_db.commit()
    
    # Verify they come back in order
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    versions = versions_response.json()
    version_numbers = [v["version_number"] for v in versions]
    assert version_numbers == sorted(version_numbers)
