"""
Mock objects and services for tests.

This module provides reusable mock implementations of services and external dependencies.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any, Optional, Callable

from app.models.file import FileChange, FileOperation
from app.services.openrouter import OpenRouterService


@pytest.fixture
def mock_openrouter_service():
    """
    Create a mock OpenRouterService for tests.
    
    This fixture creates a mock implementation of the OpenRouterService
    that doesn't make real API calls.
    
    Returns:
        MockOpenRouterService: A mock implementation of OpenRouterService
    """
    class MockOpenRouterService(MagicMock):
        """Mock implementation of OpenRouterService."""
        
        async def get_file_changes(
            self,
            project_context: str,
            change_request: str,
            current_files: List[Dict[str, Any]]
        ) -> List[FileChange]:
            """
            Return mock file changes based on the request.
            
            This method simulates different responses based on the change_request
            to make testing easier.
            
            Args:
                project_context: Context of the project
                change_request: Description of requested changes
                current_files: List of current files in the version
                
            Returns:
                List of FileChange objects
            """
            # Define test cases with specific responses
            test_cases = {
                "add_file": [
                    FileChange(
                        path="src/components/NewComponent.tsx",
                        content="export const NewComponent = () => <div>New Component</div>;",
                        operation=FileOperation.CREATE
                    )
                ],
                "update_file": [
                    FileChange(
                        path="src/App.tsx",
                        content="export const App = () => <div>Updated App</div>;",
                        operation=FileOperation.UPDATE
                    )
                ],
                "delete_file": [
                    FileChange(
                        path="src/components/HelloWorld.tsx",
                        operation=FileOperation.DELETE
                    )
                ],
                "error_case": self._raise_validation_error,
                "empty_path": self._raise_empty_path_error,
                "multi_operation": [
                    FileChange(
                        path="src/components/NewComponent.tsx",
                        content="export const NewComponent = () => <div>New Component</div>;",
                        operation=FileOperation.CREATE
                    ),
                    FileChange(
                        path="src/App.tsx",
                        content="export const App = () => <div>Updated App</div>;",
                        operation=FileOperation.UPDATE
                    ),
                    FileChange(
                        path="src/components/HelloWorld.tsx",
                        operation=FileOperation.DELETE
                    )
                ]
            }
            
            # Look for test case keywords in the change request
            for key, handler in test_cases.items():
                if key in change_request.lower():
                    if callable(handler):
                        return handler()
                    return handler
            
            # Default response for unrecognized requests
            return [
                FileChange(
                    path="src/components/DefaultComponent.tsx",
                    content="export const DefaultComponent = () => <div>Default</div>;",
                    operation=FileOperation.CREATE
                )
            ]
        
        def _raise_validation_error(self):
            """Helper to simulate validation error."""
            raise ValueError("Validation error in file changes")
            
        def _raise_empty_path_error(self):
            """Helper to simulate empty path error."""
            raise ValueError("File path cannot be empty")
    
    # Create and return mock instance
    return MockOpenRouterService()


@pytest.fixture
def patch_openrouter_service(mock_openrouter_service):
    """
    Patch the OpenRouterService get_openrouter function.
    
    This fixture patches the get_openrouter function to return
    a mock implementation, ensuring no real API calls are made.
    """
    with patch('app.services.openrouter.get_openrouter', return_value=mock_openrouter_service):
        yield mock_openrouter_service


@pytest.fixture
def mock_supabase_service():
    """
    Create a mock SupabaseService for tests.
    
    This fixture creates a mock implementation of the SupabaseService
    that doesn't make real database calls.
    
    Returns:
        MagicMock: A mock implementation of SupabaseService
    """
    mock_service = MagicMock()
    
    # Mock data for responses
    projects = [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Project 1",
            "description": "A test project",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "223e4567-e89b-12d3-a456-426614174000",
            "name": "Test Project 2",
            "description": "Another test project",
            "is_active": True,
            "created_at": "2025-01-02T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z"
        }
    ]
    
    versions = [
        {
            "id": "323e4567-e89b-12d3-a456-426614174000",
            "project_id": "123e4567-e89b-12d3-a456-426614174000",
            "version_number": 0,
            "name": "Initial Version",
            "parent_id": None,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "423e4567-e89b-12d3-a456-426614174000",
            "project_id": "123e4567-e89b-12d3-a456-426614174000",
            "version_number": 1,
            "name": "Update 1",
            "parent_id": "323e4567-e89b-12d3-a456-426614174000",
            "created_at": "2025-01-02T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z"
        }
    ]
    
    files = [
        {
            "id": "523e4567-e89b-12d3-a456-426614174000",
            "version_id": "323e4567-e89b-12d3-a456-426614174000",
            "path": "src/App.tsx",
            "content": "export const App = () => <div>App</div>;",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "623e4567-e89b-12d3-a456-426614174000",
            "version_id": "323e4567-e89b-12d3-a456-426614174000",
            "path": "src/components/HelloWorld.tsx",
            "content": "export const HelloWorld = () => <div>Hello World</div>;",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
    ]
    
    # Setup mock methods
    mock_service.list_projects.return_value = {
        "success": True,
        "data": {
            "total": len(projects),
            "items": projects,
            "skip": 0,
            "limit": 100
        }
    }
    
    mock_service.get_project.return_value = {
        "success": True,
        "data": projects[0]
    }
    
    mock_service.create_project.return_value = {
        "success": True,
        "data": projects[0]
    }
    
    mock_service.update_project.return_value = {
        "success": True,
        "data": projects[0]
    }
    
    mock_service.delete_project.return_value = {
        "success": True,
        "data": {**projects[0], "is_active": False}
    }
    
    mock_service.list_versions.return_value = {
        "success": True,
        "data": {
            "total": len(versions),
            "items": versions,
            "skip": 0,
            "limit": 100
        }
    }
    
    mock_service.get_version.return_value = {
        "success": True,
        "data": {**versions[0], "files": files}
    }
    
    mock_service.get_file.return_value = {
        "success": True,
        "data": files[0]
    }
    
    mock_service.create_or_update_file.return_value = {
        "success": True,
        "data": files[0]
    }
    
    mock_service.check_health.return_value = {
        "success": True,
        "data": {
            "status": "healthy",
            "database": "connected",
            "connection_type": "supabase"
        }
    }
    
    # Method to customize response for specific requests
    def configure_response(method_name, response):
        """Configure a custom response for a method."""
        getattr(mock_service, method_name).return_value = response
    
    mock_service.configure_response = configure_response
    
    return mock_service


@pytest.fixture
def patch_supabase_service(mock_supabase_service):
    """
    Patch the SupabaseService to return a mock.
    
    This fixture patches the SupabaseService constructor to return
    a mock implementation, ensuring no real database calls are made.
    """
    with patch('app.services.supabase.client.SupabaseService', return_value=mock_supabase_service):
        yield mock_supabase_service