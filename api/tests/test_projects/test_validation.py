import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

def test_get_nonexistent_project(client: TestClient):
    """Test getting a project that doesn't exist."""
    response = client.get("/api/projects/999")
    assert response.status_code == 422

def test_create_project_invalid_data(client: TestClient):
    """Test creating a project with invalid data."""
    response = client.post("/api/projects/", json={})
    assert response.status_code == 422

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
