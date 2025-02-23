"""
Tests for edge cases and advanced scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from app.main import app
from app.config import get_db
from app.models.project import Project, ProjectVersion, File, ProjectCreate
from app.crud import projects as crud
from tests.test_projects.conftest import test_db, test_project, test_version, test_files

def test_pagination_limits(client: TestClient, test_db: Session):
    """Test pagination edge cases for project listing."""
    # Create multiple projects
    for i in range(5):
        crud.create(test_db, ProjectCreate(name=f"Project {i}", description="Test"))
    
    # Test minimum limit
    response = client.get("/api/projects/?limit=0")
    assert response.status_code == 422  # Validation error for limit < 1
    
    # Test maximum limit
    response = client.get("/api/projects/?limit=1001")
    assert response.status_code == 422  # Validation error for limit > 1000
    
    # Test negative skip
    response = client.get("/api/projects/?skip=-1")
    assert response.status_code == 422  # Validation error for skip < 0

def test_version_number_constraints(test_db: Session):
    """Test version number constraints and edge cases."""
    # Create project directly to avoid automatic version creation
    project = Project(name="Test Project", description="Test")
    test_db.add(project)
    test_db.commit()
    
    # Test negative version number
    with pytest.raises(IntegrityError, match="Version number cannot be negative"):
        version = ProjectVersion(
            project_id=project.id,
            version_number=-1,
            name="Invalid Version"
        )
        test_db.add(version)
        test_db.commit()
    
    test_db.rollback()  # Reset session after IntegrityError
    
    # Verify latest_version_number with no versions
    assert project.latest_version_number == 0

def test_file_path_validation(test_db: Session):
    """Test file path validation edge cases."""
    # Create project directly to avoid automatic version creation
    project = Project(name="Test Project", description="Test")
    test_db.add(project)
    test_db.commit()
    
    version = ProjectVersion(
        project_id=project.id,
        version_number=1,  # Use version 1 to avoid conflict with automatic version 0
        name="Test Version"
    )
    test_db.add(version)
    test_db.commit()
    
    # Test empty path
    with pytest.raises(ValueError, match="File path cannot be empty"):
        File(
            project_version_id=version.id,
            path="",
            content="test"
        )
    
    # Test duplicate paths in same version
    file1 = File(
        project_version_id=version.id,
        path="/test.txt",
        content="test1"
    )
    test_db.add(file1)
    test_db.commit()
    
    with pytest.raises(IntegrityError):  # SQLAlchemy will raise an integrity error
        file2 = File(
            project_version_id=version.id,
            path="/test.txt",  # Same path as file1
            content="test2"
        )
        test_db.add(file2)
        test_db.commit()
    
    test_db.rollback()  # Reset session after IntegrityError

def test_version_list_pagination(client: TestClient, test_db: Session):
    """Test pagination for version listing endpoint."""
    project = crud.create(test_db, ProjectCreate(name="Test Project", description="Test"))
    
    # Create additional versions (version 0 is already created)
    for i in range(1, 5):  # Start from 1 since 0 is already created
        version = ProjectVersion(
            project_id=project.id,
            version_number=i,
            name=f"Version {i}"
        )
        test_db.add(version)
    test_db.commit()
    
    # Test invalid limit
    response = client.get(f"/api/projects/{project.id}/versions?limit=0")
    assert response.status_code == 422
    
    response = client.get(f"/api/projects/{project.id}/versions?limit=1001")
    assert response.status_code == 422
    
    # Test invalid skip
    response = client.get(f"/api/projects/{project.id}/versions?skip=-1")
    assert response.status_code == 422
    
    # Test pagination with valid parameters
    response = client.get(f"/api/projects/{project.id}/versions?skip=2&limit=2")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 3

def test_nonexistent_version_access(client: TestClient, test_db: Session):
    """Test accessing non-existent version number."""
    project_id = uuid4()
    response = client.get(f"/api/projects/{project_id}/versions/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"
    
    # Create a project to test invalid version number
    project = crud.create(test_db, ProjectCreate(name="Test Project", description="Test"))
    
    # Test invalid version number format
    response = client.get(f"/api/projects/{project.id}/versions/-1")
    assert response.status_code == 422  # Validation error for negative version
