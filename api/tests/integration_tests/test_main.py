"""
Tests for main application module.
"""
from app.main import settings
from .test_versions import get_template_files

import pytest

@pytest.mark.anyio
async def test_create_project_with_version_0(client):
    """
    Critical integration test that verifies the core project creation flow:
    1. Create a new project via API
    2. Verify version 0 is automatically created with all template files
    """
    # Create a new project
    project_data = {
        "name": "Test Project",
        "description": "Test Description"
    }
    response = await client.post(f"{settings.API_PREFIX}/projects/", json=project_data)
    assert response.status_code == 201
    project = response.json()
    assert project["name"] == project_data["name"]
    assert project["description"] == project_data["description"]
    
    # Get version 0 through the API
    project_id = project["id"]
    response = await client.get(f"{settings.API_PREFIX}/projects/{project_id}/versions/0")
    assert response.status_code == 200
    version_0 = response.json()
    
    # Verify version 0 metadata
    assert version_0["version_number"] == 0
    assert version_0["name"] == "Initial Version"
    assert version_0["parent_version_id"] is None
    
    # Get expected files from template
    expected_files = dict(get_template_files())
    
    # Verify all files exist with correct content
    assert len(version_0["files"]) == len(expected_files)
    
    # Create dictionary of actual files
    actual_files = {f["path"]: f["content"] for f in version_0["files"]}
    
    # Verify file structure matches exactly
    assert set(actual_files.keys()) == set(expected_files.keys())
    
    # Verify each file's content matches exactly
    for path, content in expected_files.items():
        assert actual_files[path] == content, f"Content mismatch for {path}"

@pytest.mark.anyio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.anyio
async def test_cors_middleware(client):
    """Test CORS middleware configuration."""
    # Test with allowed origin
    origin = "http://localhost"
    response = await client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    # FastAPI's CORSMiddleware reflects back the origin when allow_origins=["*"]
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-methods" in response.headers
    assert "GET" in response.headers["access-control-allow-methods"]
