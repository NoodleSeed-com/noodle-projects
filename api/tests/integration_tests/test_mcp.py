"""
Integration tests for the Model Context Protocol (MCP) server implementation.
These tests verify the MCP server functionality using both local and REST API implementations.
"""
import os
import uuid
import pytest
import pytest_asyncio
from typing import Dict, Any, List, Optional

# Import local test client and services for dependency injection
from app.services.openrouter import OpenRouterService, get_openrouter
from app.config import get_db, settings

# Import the MCP server implementations
try:
    from app.mcp_server_rest import (
        list_projects,
        get_project,
        create_project,
        update_project,
        delete_project,
        list_versions,
        get_version,
        create_version,
        get_file,
        create_or_update_file,
        check_health
    )
    MCP_REST_IMPORTED = True
except ImportError:
    MCP_REST_IMPORTED = False
    
try:
    # Import direct connection MCP functions if available
    from app.mcp_server import (
        list_projects as list_projects_direct,
        get_project as get_project_direct,
        create_project as create_project_direct,
        update_project as update_project_direct,
        delete_project as delete_project_direct,
        list_versions as list_versions_direct,
        get_version as get_version_direct,
        create_version as create_version_direct,
        get_file as get_file_direct,
        create_or_update_file as create_or_update_file_direct,
        check_health as check_health_direct
    )
    MCP_DIRECT_IMPORTED = True
except ImportError:
    MCP_DIRECT_IMPORTED = False

# Mark the module for skipping if MCP modules not available
pytestmark = pytest.mark.skipif(
    not (MCP_REST_IMPORTED or MCP_DIRECT_IMPORTED),
    reason="MCP server modules not available"
)

# Helper functions for test assertions
def assert_mcp_success(result: Dict[str, Any], message: str = "MCP function should return success"):
    """Assert that an MCP function result indicates success."""
    assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
    assert "success" in result, "MCP result should have 'success' key"
    assert result["success"] is True, f"{message}. Error: {result.get('error', 'Unknown error')}"
    # Some successful operations like delete might not return data
    if "data" not in result and result.get("success", False):
        # This is acceptable for certain operations
        pass
    # If data is present, validate it's a dict or None
    elif "data" in result:
        assert result["data"] is None or isinstance(result["data"], dict), "Data should be None or a dict"

def assert_project_data(project_data: Dict[str, Any], expected_name: Optional[str] = None):
    """Assert that project data has expected structure and content."""
    assert "id" in project_data, "Project data should have 'id'"
    assert "name" in project_data, "Project data should have 'name'"
    assert "description" in project_data, "Project data should have 'description'"
    assert "created_at" in project_data, "Project data should have 'created_at'"
    assert "updated_at" in project_data, "Project data should have 'updated_at'"
    assert "active" in project_data, "Project data should have 'active'"
    
    if expected_name:
        assert project_data["name"] == expected_name, f"Project name should be '{expected_name}'"

def assert_version_data(version_data: Dict[str, Any], expected_name: Optional[str] = None):
    """Assert that version data has expected structure and content."""
    assert "id" in version_data, "Version data should have 'id'"
    assert "version_number" in version_data, "Version data should have 'version_number'"
    assert "name" in version_data, "Version data should have 'name'"
    assert "project_id" in version_data, "Version data should have 'project_id'"
    assert "created_at" in version_data, "Version data should have 'created_at'"
    assert "updated_at" in version_data, "Version data should have 'updated_at'"
    
    if expected_name:
        assert version_data["name"] == expected_name, f"Version name should be '{expected_name}'"

# Test suites for MCP implementations
class TestMCPRestAPI:
    """Test suite for the MCP server REST API implementation."""
    
    # Skip the entire class if the REST API implementation is not available
    pytestmark = pytest.mark.skipif(not MCP_REST_IMPORTED, reason="MCP REST API not available")
    
    @pytest.mark.anyio
    async def test_check_health(self):
        """Test health check endpoint."""
        # Health check should return success
        result = await check_health()
        assert_mcp_success(result, "Health check should return success")
        
        # Health data should have status field (might be 'ok' or 'healthy')
        health_data = result["data"]
        assert "status" in health_data, "Health data should have 'status'"
        assert health_data["status"] in ["ok", "healthy"], f"Health status should be 'ok' or 'healthy', got '{health_data['status']}'"
        
        # Database info might be present and could be a string or dict depending on implementation
        if "database" in health_data:
            db_info = health_data["database"]
            assert isinstance(db_info, (str, dict)), f"Database info should be a string or dict, got {type(db_info)}"
            if isinstance(db_info, str):
                # String values like "connected" are acceptable
                assert len(db_info) > 0, "Database info string should not be empty"
    
    @pytest.mark.anyio
    async def test_project_lifecycle(self):
        """Test full project lifecycle from creation to deletion."""
        # Step 1: Create a project
        test_project_name = f"MCP Pytest Project {uuid.uuid4()}"
        create_result = await create_project(
            name=test_project_name,
            description="Test project created via pytest"
        )
        assert_mcp_success(create_result, "Project creation should succeed")
        project_data = create_result["data"]
        assert_project_data(project_data, test_project_name)
        project_id = project_data["id"]
        
        # Step 2: Get the project
        get_result = await get_project(project_id=project_id)
        assert_mcp_success(get_result, "Project retrieval should succeed")
        assert_project_data(get_result["data"], test_project_name)
        
        # Step 3: List projects and check if our project is there
        list_result = await list_projects()
        assert_mcp_success(list_result, "Project listing should succeed")
        projects = list_result["data"]["items"]
        assert isinstance(projects, list), "Projects should be a list"
        project_ids = [p["id"] for p in projects]
        assert project_id in project_ids, "Created project should be in list"
        
        # Step 4: Update the project
        updated_name = f"{test_project_name} - Updated"
        update_result = await update_project(
            project_id=project_id,
            name=updated_name,
            description="Updated description"
        )
        assert_mcp_success(update_result, "Project update should succeed")
        assert_project_data(update_result["data"], updated_name)
        
        # Verify the update worked
        get_updated_result = await get_project(project_id=project_id)
        assert_mcp_success(get_updated_result)
        assert get_updated_result["data"]["name"] == updated_name, "Update didn't persist"
        
        # Step 5: Delete the project
        delete_result = await delete_project(project_id=project_id)
        assert_mcp_success(delete_result, "Project deletion should succeed")
        
        # Verify the project is soft-deleted (still retrievable but inactive)
        get_deleted_result = await get_project(project_id=project_id)
        assert_mcp_success(get_deleted_result)
        assert get_deleted_result["data"]["active"] is False, "Project should be inactive after deletion"
    
    @pytest.mark.anyio
    async def test_version_and_file_operations(self):
        """Test version creation and file operations within versions."""
        # Step 1: Create a test project
        test_project_name = f"MCP Pytest File Test {uuid.uuid4()}"
        create_result = await create_project(
            name=test_project_name,
            description="Test project for version and file operations"
        )
        assert_mcp_success(create_result)
        project_id = create_result["data"]["id"]
        
        try:
            # Step 2: Create a version
            version_name = "Test Version"
            version_result = await create_version(
                project_id=project_id,
                name=version_name
            )
            assert_mcp_success(version_result, "Version creation should succeed")
            version_data = version_result["data"]
            assert_version_data(version_data, version_name)
            version_id = version_data["id"]
            
            # Step 3: Verify version via list
            list_versions_result = await list_versions(project_id=project_id)
            assert_mcp_success(list_versions_result, "Version listing should succeed")
            versions = list_versions_result["data"]["items"]
            assert len(versions) > 0, "Should have at least one version"
            version_ids = [v["id"] for v in versions]
            assert version_id in version_ids, "Created version should be in list"
            
            # Step 4: Get the version directly
            get_version_result = await get_version(version_id=version_id)
            assert_mcp_success(get_version_result, "Version retrieval should succeed")
            assert_version_data(get_version_result["data"])
            
            # Step 5: Create a file in the version
            file_path = "src/test.js"
            file_content = "// This is a test file"
            file_result = await create_or_update_file(
                version_id=version_id,
                path=file_path,
                content=file_content
            )
            assert_mcp_success(file_result, "File creation should succeed")
            file_id = file_result["data"]["id"]
            assert file_id is not None, "File should have an ID"
            
            # Step 6: Get the file
            get_file_result = await get_file(version_id=version_id, path=file_path)
            assert_mcp_success(get_file_result, "File retrieval should succeed")
            assert get_file_result["data"]["content"] == file_content, "File content should match"
            
            # Step 7: Update the file
            updated_content = file_content + "\n// Updated content"
            update_file_result = await create_or_update_file(
                version_id=version_id,
                path=file_path,
                content=updated_content
            )
            assert_mcp_success(update_file_result, "File update should succeed")
            
            # Step 8: Verify the update
            get_updated_file_result = await get_file(version_id=version_id, path=file_path)
            assert_mcp_success(get_updated_file_result)
            assert get_updated_file_result["data"]["content"] == updated_content, "Updated content should match"
            
        finally:
            # Clean up: Delete the project
            await delete_project(project_id=project_id)

# Test suite for direct database connection MCP implementation if available
@pytest.mark.skipif(not MCP_DIRECT_IMPORTED, reason="MCP direct connection not available")
class TestMCPDirectConnection:
    """Test suite for the MCP server with direct database connection."""
    
    @pytest.mark.anyio
    async def test_check_health_direct(self):
        """Test health check with direct connection."""
        if not MCP_DIRECT_IMPORTED:
            pytest.skip("MCP direct connection not available")
            
        result = await check_health_direct()
        assert_mcp_success(result, "Health check should return success")
        
        health_data = result["data"]
        assert "status" in health_data, "Health data should have 'status'"
        assert health_data["status"] == "ok", "Health status should be 'ok'"
    
    @pytest.mark.anyio
    async def test_project_lifecycle_direct(self):
        """Test project lifecycle with direct connection."""
        if not MCP_DIRECT_IMPORTED:
            pytest.skip("MCP direct connection not available")
            
        # Similar to REST API test but using the direct connection functions
        test_project_name = f"MCP Pytest Direct Project {uuid.uuid4()}"
        create_result = await create_project_direct(
            name=test_project_name,
            description="Test project created via pytest (direct)"
        )
        assert_mcp_success(create_result, "Project creation should succeed")
        project_data = create_result["data"]
        assert_project_data(project_data, test_project_name)
        project_id = project_data["id"]
        
        # Clean up
        await delete_project_direct(project_id=project_id)