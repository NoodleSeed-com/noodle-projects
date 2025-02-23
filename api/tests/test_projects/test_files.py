from fastapi.testclient import TestClient
from app.models.project import ProjectVersion, File

def test_get_specific_version_with_files(client: TestClient, test_project, test_db, test_files):
    """Test getting a specific version with parent version number and files."""
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
    test_db.flush()  # Flush to get the ID without committing
    
    # Add files to the version
    for file_data in test_files:
        file = File(
            project_version_id=child_version.id,
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

def test_version_with_no_files(client: TestClient, test_project, test_db):
    """Test that a version with no files returns an empty files array."""
    # Create a project
    create_response = client.post("/api/projects/", json=test_project)
    project_id = create_response.json()["id"]
    
    # Get the initial version (which should have no files)
    response = client.get(f"/api/projects/{project_id}/versions/0")
    assert response.status_code == 200
    data = response.json()
    
    # Verify empty files array
    assert "files" in data
    assert isinstance(data["files"], list)
    assert len(data["files"]) == 0

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
