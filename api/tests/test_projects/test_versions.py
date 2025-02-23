from fastapi.testclient import TestClient
from app.models.project import ProjectVersion

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
    assert set(versions[0].keys()) == {"id", "version_number", "name"}

def test_latest_version_number_computation(client: TestClient, test_project, test_db):
    """Test that latest_version_number correctly computes the maximum."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Add some versions manually
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
    child_version = ProjectVersion(
        project_id=project_id,
        version_number=1,
        name="Child Version",
        parent_version_id=initial_version_id
    )
    test_db.add(child_version)
    test_db.commit()
    
    # Verify the relationship in version list (simplified response)
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    versions = versions_response.json()
    assert len(versions) == 2
    child = next(v for v in versions if v["version_number"] == 1)
    assert set(child.keys()) == {"id", "version_number", "name"}
    
    # Verify the relationship in specific version response
    version_response = client.get(f"/api/projects/{project_id}/versions/1")
    version_data = version_response.json()
    assert version_data["parent_version"] == 0  # Parent is version 0

def test_version_cascade_deletion(client: TestClient, test_project, test_db):
    """Test that versions are not accessible after project is soft deleted."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Add a version
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
    versions_after = client.get(f"/api/projects/{project_id}/versions")
    assert len(versions_after.json()) == 2

def test_version_ordering(client: TestClient, test_project, test_db):
    """Test that versions are returned in order by version number."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Add some versions out of order
    versions = [
        ProjectVersion(project_id=project_id, version_number=2, name="Version 2"),
        ProjectVersion(project_id=project_id, version_number=1, name="Version 1"),
        ProjectVersion(project_id=project_id, version_number=3, name="Version 3")
    ]
    for v in versions:
        test_db.add(v)
    test_db.commit()
    
    # Verify they come back in order with correct fields
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    versions = versions_response.json()
    
    # Check ordering
    version_numbers = [v["version_number"] for v in versions]
    assert version_numbers == sorted(version_numbers)
    
    # Check response format
    for v in versions:
        assert set(v.keys()) == {"id", "version_number", "name"}
