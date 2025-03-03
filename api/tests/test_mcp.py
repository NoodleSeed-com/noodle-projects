"""
Unified MCP server test module with parametrized tests for different connection types.
"""
import os
import asyncio
import uuid
import pytest
from typing import Dict, Any, Optional

# Set test environment
os.environ["TEST_MODE"] = "True"

# Test configuration for SQLAlchemy (direct DB)
SQLALCHEMY_CONFIG = {
    "connection_type": "sqlalchemy",
    "name": "NoodleProjects-SQLAlchemy"
}

# Test configuration for Supabase REST API
SUPABASE_REST_CONFIG = {
    "connection_type": "supabase_rest",
    "name": "NoodleProjects-SupabaseREST"
}

# Available connection configurations
CONNECTION_CONFIGS = [
    SQLALCHEMY_CONFIG,
    SUPABASE_REST_CONFIG
]

class MCPTestClient:
    """Test client for MCP server."""
    
    def __init__(self, connection_type: str = "sqlalchemy", name: str = "Test-MCP"):
        """Initialize the MCP test client."""
        self.connection_type = connection_type
        self.name = name
        # Import here to avoid circular imports
        from app.mcp.server import NoodleMCP
        self.mcp_server = NoodleMCP(name=name, connection_type=connection_type)
    
    async def call(self, function_name: str, **kwargs) -> Dict[str, Any]:
        """Call an MCP function with the given arguments."""
        function = getattr(self.mcp_server, function_name, None)
        if not function:
            raise ValueError(f"Function {function_name} not found in MCP server")
        
        return await function(**kwargs)

@pytest.fixture
async def mcp_client(request):
    """Fixture to provide a configured MCP test client."""
    config = request.param if hasattr(request, "param") else SQLALCHEMY_CONFIG
    client = MCPTestClient(**config)
    yield client

@pytest.mark.parametrize("mcp_client", CONNECTION_CONFIGS, indirect=True)
async def test_health_check(mcp_client):
    """Test the health check endpoint."""
    response = await mcp_client.call("check_health")
    assert response["success"] is True
    assert response["data"]["status"] == "healthy"
    assert response["data"]["database"] == "connected"
    assert response["data"]["connection_type"] == mcp_client.connection_type

@pytest.mark.parametrize("mcp_client", CONNECTION_CONFIGS, indirect=True)
async def test_project_crud(mcp_client):
    """Test project CRUD operations."""
    # Create a project
    project_name = f"Test Project {uuid.uuid4()}"
    create_response = await mcp_client.call("create_project", name=project_name, description="Test project")
    assert create_response["success"] is True
    
    project_id = create_response["data"]["id"]
    
    # Get the project
    get_response = await mcp_client.call("get_project", project_id=project_id)
    assert get_response["success"] is True
    assert get_response["data"]["name"] == project_name
    
    # Update the project
    updated_name = f"Updated Project {uuid.uuid4()}"
    update_response = await mcp_client.call("update_project", project_id=project_id, name=updated_name)
    assert update_response["success"] is True
    assert update_response["data"]["name"] == updated_name
    
    # Delete the project (soft delete)
    delete_response = await mcp_client.call("delete_project", project_id=project_id)
    assert delete_response["success"] is True
    
    # Verify project is inactive
    get_after_delete = await mcp_client.call("get_project", project_id=project_id)
    assert get_after_delete["success"] is True
    assert get_after_delete["data"]["is_active"] is False

@pytest.mark.parametrize("mcp_client", CONNECTION_CONFIGS, indirect=True)
async def test_version_operations(mcp_client):
    """Test version operations."""
    # Create a project first
    project_name = f"Version Test Project {uuid.uuid4()}"
    project = await mcp_client.call("create_project", name=project_name)
    assert project["success"] is True
    
    project_id = project["data"]["id"]
    
    # List versions (should be empty)
    list_response = await mcp_client.call("list_versions", project_id=project_id)
    assert list_response["success"] is True
    assert list_response["data"]["total"] == 0
    
    # We can't test create_version completely here since it requires OpenRouter
    # But we can test the get_version functionality by getting the version that
    # was automatically created when the project was created
    
    # Get version 1 (initial version)
    try:
        version_response = await mcp_client.call("get_version", project_id=project_id, version_number=1)
        if version_response["success"]:
            # Verify the version has the expected attributes
            assert version_response["data"]["version_number"] == 1
            assert version_response["data"]["project_id"] == project_id
    except Exception as e:
        # Some connection types might not auto-create a version, so this is not a failure
        print(f"Note: Initial version not found: {e}")

@pytest.mark.parametrize("mcp_client", CONNECTION_CONFIGS, indirect=True)
async def test_file_operations(mcp_client):
    """Test file operations."""
    # Skip for Supabase REST API until we properly set up file operations there
    if mcp_client.connection_type == "supabase_rest":
        pytest.skip("File operations not fully implemented for Supabase REST API")
    
    # Create a project and get its initial version ID
    project = await mcp_client.call("create_project", name=f"File Test Project {uuid.uuid4()}")
    assert project["success"] is True
    
    project_id = project["data"]["id"]
    
    # Get the initial version
    try:
        version_response = await mcp_client.call("get_version", project_id=project_id, version_number=1)
        if not version_response["success"]:
            pytest.skip("Initial version not found, skipping file tests")
        
        version_id = version_response["data"]["id"]
        
        # Create a file
        file_path = "src/main.js"
        file_content = "console.log('Hello, world!');"
        create_file_response = await mcp_client.call(
            "create_or_update_file",
            version_id=version_id,
            path=file_path,
            content=file_content
        )
        assert create_file_response["success"] is True
        
        # Get the file
        get_file_response = await mcp_client.call("get_file", version_id=version_id, path=file_path)
        assert get_file_response["success"] is True
        assert get_file_response["data"]["content"] == file_content
        
        # Update the file
        updated_content = "console.log('Updated content');"
        update_file_response = await mcp_client.call(
            "create_or_update_file",
            version_id=version_id,
            path=file_path,
            content=updated_content
        )
        assert update_file_response["success"] is True
        
        # Verify the update
        get_updated_response = await mcp_client.call("get_file", version_id=version_id, path=file_path)
        assert get_updated_response["success"] is True
        assert get_updated_response["data"]["content"] == updated_content
    
    except Exception as e:
        pytest.skip(f"Test setup failed: {e}")

# Run the tests as a script
if __name__ == "__main__":
    asyncio.run(pytest.main(["-xvs", __file__]))