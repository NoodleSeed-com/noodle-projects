"""Tests for version routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ...schemas.common import FileOperation, FileChange
from ...schemas.project import ProjectCreate
from ...schemas.version import CreateVersionRequest

def test_get_version_endpoint(client: TestClient):
    """Test the GET version endpoint."""
    # Create a project and get initial version automatically created
    response = client.post("/api/projects/", json={
        "name": "Version Test Project",
        "description": "Project for testing versions"
    })
    assert response.status_code == 201
    project = response.json()
    
    # Get list of versions for the project
    response = client.get(f"/api/projects/{project['id']}/versions")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 0
    
    # Get the single version by number
    response = client.get(f"/api/projects/{project['id']}/versions/0")
    assert response.status_code == 200
    version = response.json()
    assert version["version_number"] == 0
    assert version["name"] == "Initial Version"
    assert len(version["files"]) > 0  # Should have template files
    assert "src/App.tsx" in [f["path"] for f in version["files"]]
