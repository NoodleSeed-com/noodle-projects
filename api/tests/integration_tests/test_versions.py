import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import projects, versions
from app.schemas.project import ProjectCreate

def get_template_files():
    """Helper function to get all files from the template directory."""
    # Use the same path as in crud.py
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates', 'version-0')
    
    # Print the template directory path and check if it exists
    print(f"Template directory: {template_dir}")
    print(f"Template directory exists: {os.path.exists(template_dir)}")
    if os.path.exists(template_dir):
        print("Files in template directory:", os.listdir(template_dir))
    
    files = []
    for root, _, filenames in os.walk(template_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, template_dir)
            with open(file_path, 'r') as f:
                content = f.read()
            files.append((relative_path, content))
    
    # Print found files
    print(f"Found {len(files)} template files:")
    for path, _ in files:
        print(f"  - {path}")
    
    return files

@pytest.mark.anyio
async def test_version_0_creation_with_client(client, test_project):
    """Test that version 0 is created with all template files using the API client.
    
    This test is a simpler version that uses the client fixture instead of 
    direct database access. This avoids issues with the version creation process
    in the database session.
    """
    # Create a project
    create_response = await client.post("/api/projects/", json=test_project)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Get version 0
    response = await client.get(f"/api/projects/{project_id}/versions/0")
    assert response.status_code == 200
    version_0 = response.json()
    
    # Check version properties
    assert version_0 is not None
    assert version_0["version_number"] == 0
    assert version_0["name"] == "Initial Version"
    assert version_0["parent_version"] is None
    
    # Get expected files from template
    expected_files = get_template_files()
    
    # Verify all expected files exist with correct content
    assert len(version_0["files"]) == len(expected_files)
    
    # Create dictionaries for easy comparison
    actual_files = {f["path"]: f["content"] for f in version_0["files"]}
    expected_files_dict = dict(expected_files)
    
    # Compare files
    assert set(actual_files.keys()) == set(expected_files_dict.keys())
    for path, content in expected_files_dict.items():
        assert actual_files[path] == content, f"Content mismatch for {path}"

@pytest.mark.anyio
async def test_version_0_file_structure_with_client(client, test_project):
    """Test that version 0 has the correct file structure using the API client."""
    # Create a project
    create_response = await client.post("/api/projects/", json=test_project)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Get version 0
    response = await client.get(f"/api/projects/{project_id}/versions/0")
    assert response.status_code == 200
    version_0 = response.json()
    assert version_0 is not None
    
    # Get expected paths from template directory
    expected_paths = {path for path, _ in get_template_files()}
    
    # Get actual file paths
    actual_paths = {f["path"] for f in version_0["files"]}
    
    # Compare paths
    assert actual_paths == expected_paths, "File structure does not match template directory"

@pytest.mark.anyio
async def test_version_0_file_contents_match_templates_with_client(client, test_project):
    """Test that all file contents exactly match the templates using the API client."""
    # Create a project
    create_response = await client.post("/api/projects/", json=test_project)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Get version 0
    response = await client.get(f"/api/projects/{project_id}/versions/0")
    assert response.status_code == 200
    version_0 = response.json()
    assert version_0 is not None
    
    # Get template files
    template_files = get_template_files()
    
    # Create a map of version files for easy access
    version_files = {f["path"]: f["content"] for f in version_0["files"]}
    
    # Compare each template file with the version file
    for template_path, template_content in template_files:
        assert template_path in version_files, f"Missing file: {template_path}"
        assert version_files[template_path] == template_content, f"Content mismatch in {template_path}"
