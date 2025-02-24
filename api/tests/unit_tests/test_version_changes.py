"""Unit tests for version changes using OpenRouter service."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.crud import projects
from app.models.project import (
    ProjectCreate,
    CreateVersionRequest,
    FileOperation,
    FileChange
)

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

def test_create_version_with_changes(mock_db: Session, mock_openrouter, client: TestClient):
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
