"""Unit tests for edge cases and error scenarios using mocked OpenRouter service."""
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from unittest.mock import MagicMock
from app.models.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectVersionResponse,
    FileOperation,
    FileChange
)
from app.crud import projects
from app.main import app
from app.services.openrouter import get_openrouter
from tests.common.test_helpers import (
    run_concurrent_requests,
    assert_unique_responses,
    assert_response_mix,
    assert_database_constraints,
    assert_file_constraints
)

def test_partial_version_creation_rollback(client: TestClient, mock_db: Session, mock_openrouter):
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
    async def mock_service():
        mock = MagicMock()
        mock.get_file_changes.side_effect = ValueError("Duplicate file paths found in changes")
        return mock
    
    # Override the dependency
    app.dependency_overrides[get_openrouter] = mock_service
    
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

def test_concurrent_connection_pool_exhaustion(client: TestClient, mock_db: Session, mock_openrouter):
    """Test behavior when connection pool is exhausted.
    
    Verifies:
    1. System handles pool exhaustion gracefully
    2. Requests queue properly
    3. No deadlocks occur
    4. Error responses are correct
    """
    # Create test project
    response = client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing pool exhaustion"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Configure mock for many version creations
    mock_openrouter.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    
    # Function to create version
    def create_version(i: int):
        return client.post(
            f"/api/projects/{project_id}/versions",
            json={
                "name": f"Version {i}",
                "parent_version_number": 0,
                "project_context": "Testing pool",
                "change_request": "Create version"
            }
        )
    
    # Create many versions concurrently to exhaust pool
    responses = run_concurrent_requests(
        client,
        create_version,
        count=3,
        max_workers=3
    )
    
    # Some requests should succeed, others should fail gracefully
    success_count = sum(1 for r in responses if r.status_code == 200)
    error_count = sum(1 for r in responses if r.status_code in (503, 429))
    
    assert success_count > 0, "No requests succeeded"
    assert error_count > 0, "No requests failed due to pool exhaustion"
    assert all(r.status_code in (200, 503, 429) for r in responses)

def test_concurrent_version_state_race(client: TestClient, mock_db: Session, mock_openrouter):
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

def test_idempotent_version_creation(client: TestClient, mock_db: Session, mock_openrouter):
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

def test_file_operation_compensation(client: TestClient, mock_db: Session, mock_openrouter):
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
