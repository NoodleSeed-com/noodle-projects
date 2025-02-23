import os
from unittest.mock import patch, MagicMock
from uuid import UUID
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.crud import projects
from app.models.project import (
    ProjectCreate,
    ProjectVersion,
    File,
    CreateVersionRequest,
    FileOperation,
    FileChange
)
from app.main import app

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

def test_version_0_creation(test_db: Session):
    """Test that version 0 is created with all template files."""
    # Create a test project
    project = projects.create(test_db, ProjectCreate(
        name="Test Project",
        description="Test Description"
    ))
    
    # Get version 0
    version_0 = projects.get_version(test_db, project.id, 0)
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

def test_version_0_file_structure(test_db: Session):
    """Test that version 0 has the correct file structure."""
    # Create a test project
    project = projects.create(test_db, ProjectCreate(
        name="Test Project",
        description="Test Description"
    ))
    
    # Get version 0
    version_0 = projects.get_version(test_db, project.id, 0)
    assert version_0 is not None
    
    # Get expected paths from template directory
    expected_paths = {path for path, _ in get_template_files()}
    
    # Get actual file paths
    actual_paths = {f.path for f in version_0.files}
    
    # Compare paths
    assert actual_paths == expected_paths, "File structure does not match template directory"

def test_version_0_file_contents_match_templates(test_db: Session):
    """Test that all file contents exactly match the templates."""
    # Create a test project
    project = projects.create(test_db, ProjectCreate(
        name="Test Project",
        description="Test Description"
    ))
    
    # Get version 0
    version_0 = projects.get_version(test_db, project.id, 0)
    assert version_0 is not None
    
    # Get template files
    template_files = get_template_files()
    
    # Create a map of version files for easy access
    version_files = {f.path: f.content for f in version_0.files}
    
    # Compare each template file with the version file
    for template_path, template_content in template_files:
        assert template_path in version_files, f"Missing file: {template_path}"
        assert version_files[template_path] == template_content, f"Content mismatch in {template_path}"

@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter service."""
    with patch("app.services.openrouter.OpenRouterService") as MockService:
        # Create mock instance
        mock_service = MockService.return_value
        # Set up mock response
        mock_service.get_file_changes.return_value = [
            FileChange(
                operation=FileOperation.CREATE,
                path="src/NewComponent.tsx",
                content="export const NewComponent = () => <div>New Component</div>"
            ),
            FileChange(
                operation=FileOperation.UPDATE,
                path="src/App.tsx",
                content="import { NewComponent } from './NewComponent';\n\nexport const App = () => <NewComponent />;"
            ),
            FileChange(
                operation=FileOperation.DELETE,
                path="src/components/HelloWorld.tsx"
            )
        ]
        yield mock_service

def test_create_version_with_changes(test_db: Session, mock_openrouter, client: TestClient):
    """Test creating a new version with AI-generated changes."""
    # Create initial project with version 0
    project = projects.create(test_db, ProjectCreate(
        name="Test Project",
        description="Test Description"
    ))
    test_db.commit()  # Ensure changes are committed
    
    # Create version request
    request = CreateVersionRequest(
        name="Updated Version",
        parent_version_number=0,
        project_context="React project that needs a new component",
        change_request="Add a new component and update App.tsx to use it"
    ).model_dump()
    
    # Make the request
    response = client.post(
        f"/api/projects/{project.id}/versions",
        json=request
    )
    
    # Print response for debugging
    print("\nResponse:", response.status_code)
    print("Response body:", response.json())
    print("Mock called:", mock_openrouter.get_file_changes.called)
    print("Mock return value:", mock_openrouter.get_file_changes.return_value)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Version"
    assert data["version_number"] == 1
    assert data["parent_version"] == 0
    
    # Verify file changes
    files = {f["path"]: f for f in data["files"]}
    
    # New file was created
    assert "src/NewComponent.tsx" in files
    assert files["src/NewComponent.tsx"]["content"] == "export const NewComponent = () => <div>New Component</div>"
    
    # Existing file was updated
    assert "src/App.tsx" in files
    assert files["src/App.tsx"]["content"] == "import { NewComponent } from './NewComponent';\n\nexport const App = () => <NewComponent />;"
    
    # File was deleted
    assert "src/components/HelloWorld.tsx" not in files
    
    # Verify OpenRouter service was called correctly
    mock_openrouter.get_file_changes.assert_called_once()
    call_args = mock_openrouter.get_file_changes.call_args[1]  # Get kwargs
    assert call_args["project_context"] == "React project that needs a new component"
    assert call_args["change_request"] == "Add a new component and update App.tsx to use it"
    assert len(call_args["current_files"]) > 0  # Verify files were passed
