"""Integration tests for concurrent operations in the FastAPI service."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.common.test_helpers import (
    run_concurrent_requests,
    assert_response_mix
)

async def test_concurrent_state_changes(client: TestClient):
    """Test concurrent project state changes.
    
    Verifies:
    1. State changes are handled atomically
    2. Race conditions are prevented
    3. Final state is consistent
    4. All versions reflect correct state
    """
    # Create test project
    response = await client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Testing state changes"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # Make concurrent state change requests
    async def change_state(i: int):
        return await client.put(
            f"/api/projects/{project_id}",
            json={"active": i % 2 == 0}
        )
    
    responses = await run_concurrent_requests(client, change_state, count=3)
    
    # Verify mix of success and conflict responses
    assert_response_mix(responses, [200, 409])
    
    # Wait for all responses to complete before checking final state
    for response in responses:
        if response.status_code == 200:
            # Wait for transaction to complete
            await client.get(f"/api/projects/{project_id}")
    
    # Get final state
    final_response = await client.get(f"/api/projects/{project_id}")
    assert final_response.status_code == 200
    final_state = final_response.json()
    assert isinstance(final_state["active"], bool)
    
    # Check all versions inherit project state
    versions_response = await client.get(f"/api/projects/{project_id}/versions")
    assert versions_response.status_code == 200
    for version in versions_response.json():
        version_detail = await client.get(
            f"/api/projects/{project_id}/versions/{version['version_number']}"
        )
        assert version_detail.status_code == 200
        assert version_detail.json()["active"] == final_state["active"]
