import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import projects
from app.models.project import ProjectCreate

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
async def test_version_0_creation(test_db: AsyncSession):
    """Test that version 0 is created with all template files."""
    # Create a test project
    project = await projects.create(test_db, ProjectCreate(
        name="Test Project",
        description="Test Description"
    ))
    
    # Get version 0
    version_0 = await projects.get_version(test_db, project.id, 0)
    assert version_0 is not None
    assert version_0.version_number == 0
    assert version_0.name == "Initial Version"
    assert version_0.parent_version_id is None
    
    # Get expected files from template
    expected_files = get_template_files()
    
    # Verify all expected files exist with correct content
    assert len(version_0.files) == len(expected_files)
    
    # Create dictionaries for easy comparison
    actual_files = {f.path: f.content for f in version_0.files}
    expected_files_dict = dict(expected_files)
    
    # Compare files
    assert set(actual_files.keys()) == set(expected_files_dict.keys())
    for path, content in expected_files_dict.items():
        assert actual_files[path] == content, f"Content mismatch for {path}"

@pytest.mark.anyio
async def test_version_0_file_structure(test_db: AsyncSession):
    """Test that version 0 has the correct file structure."""
    # Create a test project
    project = await projects.create(test_db, ProjectCreate(
        name="Test Project",
        description="Test Description"
    ))
    
    # Get version 0
    version_0 = await projects.get_version(test_db, project.id, 0)
    assert version_0 is not None
    
    # Get expected paths from template directory
    expected_paths = {path for path, _ in get_template_files()}
    
    # Get actual file paths
    actual_paths = {f.path for f in version_0.files}
    
    # Compare paths
    assert actual_paths == expected_paths, "File structure does not match template directory"

@pytest.mark.anyio
async def test_version_0_file_contents_match_templates(test_db: AsyncSession):
    """Test that all file contents exactly match the templates."""
    # Create a test project
    project = await projects.create(test_db, ProjectCreate(
        name="Test Project",
        description="Test Description"
    ))
    
    # Get version 0
    version_0 = await projects.get_version(test_db, project.id, 0)
    assert version_0 is not None
    
    # Get template files
    template_files = get_template_files()
    
    # Create a map of version files for easy access
    version_files = {f.path: f.content for f in version_0.files}
    
    # Compare each template file with the version file
    for template_path, template_content in template_files:
        assert template_path in version_files, f"Missing file: {template_path}"
        assert version_files[template_path] == template_content, f"Content mismatch in {template_path}"
