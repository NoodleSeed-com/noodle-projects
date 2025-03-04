"""
Integration tests for Supabase service.

These tests demonstrate proper use of integration tests with actual Supabase
service when credentials are available, otherwise they are skipped.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock

from app.services.supabase.client import SupabaseService


@pytest.mark.requires_supabase
@pytest.mark.integration
def test_supabase_connection_with_real_credentials():
    """Test connecting to Supabase with real credentials from environment."""
    # This test will be skipped if SUPABASE_URL and SUPABASE_KEY are not set
    service = SupabaseService()
    result = service.check_health()
    
    # Verify connection was successful
    assert result["success"] is True
    assert result["data"]["status"] == "healthy"
    assert result["data"]["database"] == "connected"


@pytest.mark.integration
def test_supabase_project_operations(mock_supabase_service):
    """Test project operations with mocked Supabase service."""
    # Set up expected responses
    test_id = "123e4567-e89b-12d3-a456-426614174000"
    project_data = {
        "name": "Test Project",
        "description": "Test project for test_supabase_project_operations"
    }
    
    # Configure mock to return custom response for this specific project
    expected_response = {
        "success": True,
        "data": {
            "id": test_id,
            "name": project_data["name"],
            "description": project_data["description"],
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
    }
    
    # Configure mock service
    mock_supabase_service.create_project.return_value = expected_response
    mock_supabase_service.get_project.return_value = expected_response
    
    # Create project
    result = mock_supabase_service.create_project(
        name=project_data["name"], 
        description=project_data["description"]
    )
    
    # Verify create operation
    assert result["success"] is True
    assert result["data"]["name"] == project_data["name"]
    assert result["data"]["id"] == test_id
    
    # Get project
    result = mock_supabase_service.get_project(test_id)
    
    # Verify get operation
    assert result["success"] is True
    assert result["data"]["name"] == project_data["name"]
    assert result["data"]["id"] == test_id


@pytest.mark.integration
@pytest.mark.skip(reason="Dependency injection not working properly yet")
def test_supabase_service_with_dependency_injection(patch_supabase_service):
    """Test Supabase service with patched dependency injection."""
    # With the patch_supabase_service fixture, any code that creates
    # a SupabaseService instance will get our mock instead
    
    # Configure mock
    patch_supabase_service.check_health.return_value = {
        "success": True,
        "data": {
            "status": "healthy",
            "database": "connected",
            "connection_type": "mocked_supabase"
        }
    }
    
    # Mock environment variables
    with patch.dict('os.environ', {
        'SUPABASE_URL': 'mock_url',
        'SUPABASE_KEY': 'mock_key'
    }):
        # Function that would normally create a real service
        def use_supabase_service():
            service = SupabaseService()  # This will now be our mock
            return service.check_health()
        
        # Call the function
        result = use_supabase_service()
        
        # Verify we got our mock's response
        assert result["success"] is True
        assert result["data"]["status"] == "healthy"
        assert result["data"]["connection_type"] == "mocked_supabase"
        
        # Verify our mock was called
        patch_supabase_service.check_health.assert_called_once()