"""Tests for project routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ...schemas.common import FileOperation, FileChange
from ...schemas.project import ProjectResponse
from ...schemas.version import VersionResponse
from tests.common.test_helpers import (
    run_concurrent_requests,
    assert_unique_responses,
    assert_response_mix,
    assert_database_constraints,
    assert_file_constraints
)

def test_inactive_project_operations(client: TestClient, mock_openrouter):
    """Test operations on inactive projects.
    
    Verifies:
    1. Cannot create new versions on inactive project
    2. Cannot modify inactive project
    3. Cannot perform any write operations
    4. Proper error responses returned with correct structure
    """
    # Create and deactivate a project
    project = client.post("/api/projects/", json={
        "name": "Inactive Project",
        "description": "Test Description"
    }).json()
    
    delete_response = client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 200
    inactive_project = delete_response.json()
    project_id = inactive_project["id"]

    # Test all write operations
    operations = [
        # Attempt to create version
        ("POST", f"/api/projects/{project_id}/versions", {
            "name": "New Feature",
            "parent_version_number": 0,
            "project_context": "Adding feature to inactive project",
            "change_request": "Create feature"
        }),
        # Attempt to modify project
        ("PUT", f"/api/projects/{project_id}", {
            "name": "New Name",
            "description": "New description"
        })
    ]

    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/Feature.tsx",
            content="export const Feature = () => <div>Feature</div>"
        )
    ]

    # Verify all operations fail with proper error structure
    for method, url, data in operations:
        response = client.request(method, url, json=data)
        assert response.status_code == 403
        error = response.json()
        assert "detail" in error
        assert "inactive" in error["detail"].lower()
        assert isinstance(error["detail"], str)

def test_inactive_version_operations(client: TestClient, mock_openrouter):
    """Test operations on versions of inactive projects.
    
    Verifies:
    1. Cannot create new versions from inactive project versions
    2. Read operations still work but show inactive state
    3. Error responses have correct structure
    """
    # Create project with version
    project = client.post("/api/projects/", json={
        "name": "Project with Version",
        "description": "Test Description"
    }).json()

    # Create version
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/Feature.tsx",
            content="export const Feature = () => <div>Feature</div>"
        )
    ]
    version_response = client.post(
        f"/api/projects/{project['id']}/versions",
        json={
            "name": "Test Version",
            "parent_version_number": 0,
            "project_context": "Adding feature",
            "change_request": "Create feature"
        }
    )
    assert version_response.status_code == 200
    version = version_response.json()
    project_id = project["id"]
    version_number = version["version_number"]

    # Soft delete project
    client.delete(f"/api/projects/{project_id}")

    # Attempt to create new version from inactive project's version
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/NewFeature.tsx",
            content="export const NewFeature = () => <div>New Feature</div>"
        )
    ]
    
    response = client.post(
        f"/api/projects/{project_id}/versions",
        json={
            "name": "New Feature",
            "parent_version_number": version_number,
            "project_context": "Adding feature to inactive project",
            "change_request": "Create feature"
        }
    )
    assert response.status_code == 403
    error = response.json()
    assert "detail" in error
    assert "inactive" in error["detail"].lower()
    assert isinstance(error["detail"], str)

    # Verify read operations work but show inactive state
    version_response = client.get(f"/api/projects/{project_id}/versions/{version_number}")
    assert version_response.status_code == 200
    version_data = version_response.json()
    version = VersionResponse(**version_data)
    assert version.active is False

def test_partial_version_creation_rollback(client: TestClient, mock_openrouter):
    """Test transaction rollback on partial version creation failure.
    
    Verifies:
    1. Transaction is rolled back on error
    2. No partial state remains
    3. Database remains consistent
    4. Error is properly reported
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing rollback"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock service to raise ValueError
    mock_openrouter.get_file_changes.side_effect = ValueError("Duplicate file paths found in changes")
    
    # Attempt version creation that will fail
    response = client.post(
        f"/api/projects/{project_id}/versions",
        json={
            "name": "Failed Version",
            "parent_version_number": 0,
            "project_context": "Testing rollback",
            "change_request": "Create invalid version"
        }
    )
    assert response.status_code == 400
    
    # Verify no version was created
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) == 1  # Only initial version exists

def test_concurrent_version_state_race(client: TestClient, mock_openrouter):
    """Test race conditions in version state updates.
    
    Verifies:
    1. No lost updates occur
    2. State remains consistent
    3. Proper error handling
    4. Transaction isolation works
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing state races"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Create initial version
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    
    version_response = client.post(
        f"/api/projects/{project_id}/versions",
        json={
            "name": "Test Version",
            "parent_version_number": 0,
            "project_context": "Testing races",
            "change_request": "Create version"
        }
    )
    assert version_response.status_code == 200
    version = version_response.json()
    
    # Try to update version state concurrently
    def update_state(i: int):
        return client.put(
            f"/api/projects/{project_id}/versions/{version['version_number']}",
            json={"name": f"Updated Name {i}"}
        )
    
    responses = run_concurrent_requests(client, update_state, count=3, max_workers=3)
    
    # Verify one update succeeded, others failed with conflict
    success_responses = [r for r in responses if r.status_code == 200]
    assert len(success_responses) == 1
    
    # Check final state
    final_response = client.get(
        f"/api/projects/{project_id}/versions/{version['version_number']}"
    )
    assert final_response.status_code == 200
    final_state = final_response.json()
    assert final_state["name"].startswith("Updated Name")

def test_idempotent_version_creation(client: TestClient, mock_openrouter):
    """Test idempotent version creation under concurrent requests.
    
    Verifies:
    1. Duplicate requests are handled properly
    2. No duplicate versions are created
    3. Response is consistent for duplicates
    4. Database remains consistent
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing idempotency"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    
    # Create same version concurrently with idempotency key
    def create_version(i: int):
        return client.post(
            f"/api/projects/{project_id}/versions",
            json={
                "name": "Same Version",
                "parent_version_number": 0,
                "project_context": "Testing idempotency",
                "change_request": "Create version",
                "idempotency_key": "test-key"  # Same key for all requests
            }
        )
    
    responses = run_concurrent_requests(client, create_version, count=3, max_workers=3)
    
    # All requests should return same version
    success_responses = [r for r in responses if r.status_code == 200]
    assert len(success_responses) > 0
    
    # All successful responses should have same version number
    version_numbers = [r.json()["version_number"] for r in success_responses]
    assert len(set(version_numbers)) == 1
    
    # Verify only one version was created
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) == 2  # Initial version + 1 new version

def test_file_operation_compensation(client: TestClient, mock_openrouter):
    """Test compensation for failed file operations.
    
    Verifies:
    1. Failed operations are properly compensated
    2. No orphaned files remain
    3. Database state is consistent
    4. Error responses are correct
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing compensation"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock for initial version
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    
    # Create initial version
    version_response = client.post(
        f"/api/projects/{project_id}/versions",
        json={
            "name": "Test Version",
            "parent_version_number": 0,
            "project_context": "Testing compensation",
            "change_request": "Create version"
        }
    )
    assert version_response.status_code == 200
    version = version_response.json()
    
    # Try to create multiple files where some will fail
    def create_file(i: int):
        return client.post(
            f"/api/projects/{project_id}/versions/{version['version_number']}/files",
            json={
                "path": f"src/test{i}.tsx",
                "content": "invalid" if i % 2 == 0 else "valid content"
            }
        )
    
    responses = run_concurrent_requests(client, create_file, count=3, max_workers=3)
    
    # Verify mix of success and failure
    success_responses = [r for r in responses if r.status_code == 201]
    error_responses = [r for r in responses if r.status_code != 201]
    assert len(success_responses) > 0
    assert len(error_responses) > 0
    
    # Check final version state
    final_response = client.get(
        f"/api/projects/{project_id}/versions/{version['version_number']}"
    )
    assert final_response.status_code == 200
    final_state = final_response.json()
    
    # Only valid files should exist
    for i in range(4):
        files = [f for f in final_state["files"] if f["path"] == f"src/test{i}.tsx"]
        if i % 2 == 0:
            assert len(files) == 0  # Invalid files should not exist
        else:
            assert len(files) == 1  # Valid files should exist
