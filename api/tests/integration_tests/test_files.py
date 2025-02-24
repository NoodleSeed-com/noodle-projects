from fastapi.testclient import TestClient
from app.models.project import Version, File
from sqlalchemy.exc import IntegrityError
import pytest

def test_get_specific_version_with_files(client: TestClient, test_project, test_db, test_files):
    """Test getting a specific version with parent version number and files."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Get the initial version's ID
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    initial_version_id = versions_response.json()[0]["id"]
    
    # Create a child version
    child_version = Version(
        project_id=project_id,
        version_number=1,
        name="Child Version",
        parent_version_id=initial_version_id
    )
    test_db.add(child_version)
    test_db.flush()  # Flush to get the ID without committing
    
    # Add files to the version
    for file_data in test_files:
        file = File(
            version_id=child_version.id,
            path=file_data["path"],
            content=file_data["content"]
        )
        test_db.add(file)
    test_db.commit()
    
    # Get the specific version
    response = client.get(f"/api/projects/{project_id}/versions/1")
    assert response.status_code == 200
    data = response.json()
    
    # Verify response format and content
    assert data["version_number"] == 1
    assert data["name"] == "Child Version"
    assert data["parent_version"] == 0  # Parent is version 0
    assert "parent_version_id" in data
    assert data["parent_version_id"] == initial_version_id
    
    # Verify files
    assert "files" in data
    assert len(data["files"]) == len(test_files)
    for file_data, response_file in zip(test_files, data["files"]):
        assert "id" in response_file
        assert response_file["path"] == file_data["path"]
        assert response_file["content"] == file_data["content"]

def test_version_0_template_files(client: TestClient, test_project, test_db):
    """Test that version 0 contains all files from the template directory."""
    import os
    from pathlib import Path

    # Get template files (excluding directories)
    template_dir = "templates/version-0"
    expected_paths = set()
    for root, _, files in os.walk(template_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, template_dir)
            expected_paths.add(relative_path)
    
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Get version 0 which should have template files
    response = client.get(f"/api/projects/{project_id}/versions/0")
    assert response.status_code == 200
    data = response.json()
    
    # Verify files array contains all template files
    assert "files" in data
    assert isinstance(data["files"], list)
    
    # Verify all template files are present
    actual_paths = {file["path"] for file in data["files"]}
    assert actual_paths == expected_paths

def test_get_project_with_versions_and_files(client: TestClient, test_project, test_db):
    """Test retrieving a project with associated versions and files."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Retrieve the project
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["latest_version_number"] == 0

    # Retrieve the project versions
    response_2 = client.get(f"/api/projects/{project_id}/versions")
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert len(data_2) == 1
    # Verify simplified version list response
    version = data_2[0]
    assert set(version.keys()) == {"id", "version_number", "name"}
    assert version["version_number"] == 0
    assert version["name"] == "Initial Version"

    # Get specific version
    response_3 = client.get(f"/api/projects/{project_id}/versions/0")
    assert response_3.status_code == 200
    version_data = response_3.json()
    assert version_data["version_number"] == 0
    assert version_data["name"] == "Initial Version"
    assert version_data["parent_version"] is None
    assert "files" in version_data
    assert isinstance(version_data["files"], list)

def test_empty_file_path_validation(client: TestClient, test_project, test_db):
    """Test that empty file paths are rejected."""
    # Create project and version
    project_response = client.post("/api/projects/", json=test_project)
    project_id = project_response.json()["id"]
    version_id = client.get(f"/api/projects/{project_id}/versions").json()[0]["id"]
    
    # Test empty path
    with pytest.raises(ValueError) as exc_info:
        File(
            version_id=version_id,
            path="",
            content="test content"
        )
    assert str(exc_info.value) == "File path cannot be empty"

def test_duplicate_file_paths(client: TestClient, test_project, test_db):
    """Test that duplicate file paths in the same version are rejected."""
    # Create project and version
    project_response = client.post("/api/projects/", json=test_project)
    project_id = project_response.json()["id"]
    version_id = client.get(f"/api/projects/{project_id}/versions").json()[0]["id"]
    
    # Create first file
    file1 = File(
        version_id=version_id,
        path="/test.txt",
        content="content 1"
    )
    test_db.add(file1)
    test_db.commit()
    
    # Attempt to create second file with same path
    file2 = File(
        version_id=version_id,
        path="/test.txt",  # Same path
        content="content 2"
    )
    test_db.add(file2)
    with pytest.raises(IntegrityError) as exc_info:
        test_db.commit()
    assert "unique_version_path" in str(exc_info.value)
    test_db.rollback()

def test_file_content_null_validation(client: TestClient, test_project, test_db):
    """Test that null/missing file content is rejected but empty string is allowed."""
    # Create project and version
    project_response = client.post("/api/projects/", json=test_project)
    project_id = project_response.json()["id"]
    version_id = client.get(f"/api/projects/{project_id}/versions").json()[0]["id"]
    
    # Test that empty string is allowed
    file = File(
        version_id=version_id,
        path="/empty.txt",
        content=""
    )
    test_db.add(file)
    test_db.commit()
    
    # Verify empty content was stored
    response = client.get(f"/api/projects/{project_id}/versions/0")
    assert response.status_code == 200
    stored_file = next(f for f in response.json()["files"] if f["path"] == "/empty.txt")
    assert stored_file["content"] == ""
    
    # Test that None/null is not allowed
    with pytest.raises(ValueError) as exc_info:
        File(
            version_id=version_id,
            path="/test.txt",
            content=None
        )
    assert "content" in str(exc_info.value)
    
def test_file_content_limits(client: TestClient, test_project, test_db):
    """Test handling of file content up to 1MB."""
    # Create project and version
    project_response = client.post("/api/projects/", json=test_project)
    project_id = project_response.json()["id"]
    version_id = client.get(f"/api/projects/{project_id}/versions").json()[0]["id"]
    
    # Test 1MB file content
    content = "x" * (1 * 1024 * 1024)  # 1MB
    file = File(
        version_id=version_id,
        path="/large.txt",
        content=content
    )
    test_db.add(file)
    test_db.commit()
    
    # Verify content was stored correctly
    response = client.get(f"/api/projects/{project_id}/versions/0")
    assert response.status_code == 200
    stored_file = next(f for f in response.json()["files"] if f["path"] == "/large.txt")
    assert len(stored_file["content"]) == len(content)
