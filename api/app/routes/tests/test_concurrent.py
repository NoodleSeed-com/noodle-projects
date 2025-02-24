"""Tests for concurrent API operations."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ...schemas.common import FileOperation, FileChange
from tests.common.test_helpers import (
    run_concurrent_requests,
    assert_unique_responses,
    assert_database_constraints,
    assert_file_constraints,
    assert_response_mix
)

def test_concurrent_version_creation(client: TestClient, mock_openrouter):
    """Test concurrent version creation.
    
    Verifies:
    1. Multiple versions can be created concurrently
    2. Version numbers are assigned correctly
    3. No duplicate version numbers are created
    4. Database constraints are maintained
    5. OpenRouter service is called correctly
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing concurrent version creation"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock for multiple version creation
    mock_openrouter.get_file_changes.side_effect = [
        [FileChange(
            operation=FileOperation.CREATE,
            path=f"src/Feature{i}.tsx",
            content=f"export const Feature{i} = () => <div>Feature {i}</div>"
        )] for i in range(3)
    ]
    
    # Create multiple versions concurrently
    def create_version(i: int):
        return client.post(
            f"/api/projects/{project_id}/versions",
            json={
                "name": f"Version {i}",
                "parent_version_number": 0,
                "project_context": f"Adding Feature {i}",
                "change_request": f"Create Feature {i} component"
            }
        )
    
    responses = run_concurrent_requests(client, create_version, count=3, max_workers=3)
    
    # Verify responses and database state
    assert all(r.status_code == 200 for r in responses)
    assert_unique_responses(responses, "version_number")
    assert_database_constraints(responses, client, project_id)
    
    # Verify OpenRouter service calls
    assert mock_openrouter.get_file_changes.call_count == 3
    for i, call in enumerate(mock_openrouter.get_file_changes.call_args_list):
        args = call.kwargs
        assert args["project_context"] == f"Adding Feature {i}"
        assert args["change_request"] == f"Create Feature {i} component"
    
    # Verify file creation in each version
    for i, response in enumerate(responses):
        version_detail = client.get(
            f"/api/projects/{project_id}/versions/{response.json()['version_number']}"
        )
        assert version_detail.status_code == 200
        version_data = version_detail.json()
        feature_file = next(
            f for f in version_data["files"] 
            if f["path"] == f"src/Feature{i}.tsx"
        )
        assert feature_file["content"] == f"export const Feature{i} = () => <div>Feature {i}</div>"

def test_version_creation_constraints(client: TestClient, mock_openrouter):
    """Test version creation constraints and error handling.
    
    Verifies:
    1. Version number uniqueness is enforced
    2. Parent version validation works
    3. Database constraints prevent invalid states
    4. Error responses are correct
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing version constraints"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock for version creation attempts
    mock_openrouter.get_file_changes.side_effect = [
        [FileChange(
            operation=FileOperation.CREATE,
            path=f"src/Version{i}.tsx",
            content=f"export const Version{i} = () => <div>Version {i}</div>"
        )] for i in range(5)
    ]
    
    # Try concurrent version creation with same parent
    def create_version(i: int):
        return client.post(
            f"/api/projects/{project_id}/versions",
            json={
                "name": f"Version {i}",
                "parent_version_number": 0,
                "project_context": "Test context",
                "change_request": "Test request"
            }
        )
    
    responses = run_concurrent_requests(client, create_version, count=3, max_workers=3)
    
    # Verify unique version numbers and database state
    assert all(r.status_code == 200 for r in responses)
    assert_unique_responses(responses, "version_number")
    assert_database_constraints(responses, client, project_id)
    
    # Try to create version with non-existent parent
    invalid_response = client.post(
        f"/api/projects/{project_id}/versions",
        json={
            "name": "Invalid Version",
            "parent_version_number": 999,
            "project_context": "Test context",
            "change_request": "Test request"
        }
    )
    assert invalid_response.status_code == 404

def test_file_operation_constraints(client: TestClient, mock_openrouter):
    """Test file operation constraints and concurrent access.
    
    Verifies:
    1. File path uniqueness is enforced
    2. File content validation works
    3. Database constraints are maintained
    4. Error handling is correct
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing file operations"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock for file operations
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    
    # Create a version to test file operations
    version_response = client.post(
        f"/api/projects/{project_id}/versions",
        json={
            "name": "File Test Version",
            "parent_version_number": 0,
            "project_context": "Testing file operations",
            "change_request": "Add test component"
        }
    )
    assert version_response.status_code == 200
    version = version_response.json()
    
    # Try concurrent file creation with same path
    def create_file(i: int):
        return client.post(
            f"/api/projects/{project_id}/versions/{version['version_number']}/files",
            json={
                "path": "src/shared.tsx",
                "content": f"content_{i}"
            }
        )
    
    file_responses = run_concurrent_requests(client, create_file, count=3, max_workers=3)
    
    # Verify one success and conflicts for duplicates
    assert_response_mix(file_responses, [201, 409])
    success_responses = [r for r in file_responses if r.status_code == 201]
    assert len(success_responses) == 1
    
    # Verify file constraints
    assert_file_constraints(
        file_responses,
        client,
        project_id,
        version["version_number"],
        "src/shared.tsx"
    )
    
    # Try to create file in non-existent version
    invalid_response = client.post(
        f"/api/projects/{project_id}/versions/999/files",
        json={
            "path": "src/invalid.tsx",
            "content": "invalid content"
        }
    )
    assert invalid_response.status_code == 404
