"""
Client fixtures for API testing.

This module provides fixtures for testing the FastAPI application endpoints.
"""
import pytest
import pytest_asyncio
from typing import Dict, Any, AsyncGenerator, Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import get_db


@pytest.fixture
def client(db_session) -> TestClient:
    """
    Create a TestClient for synchronous API testing.
    
    This fixture creates a FastAPI TestClient connected to a test database.
    The client's requests use a transaction that is rolled back after each test.
    
    Returns:
        TestClient: A FastAPI test client
    """
    # Override database dependency
    def override_get_db():
        return db_session
    
    original_dependencies = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Restore original dependencies
    app.dependency_overrides = original_dependencies


@pytest_asyncio.fixture
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient for asynchronous API testing.
    
    This fixture creates an async HTTP client connected to a test database.
    The client's requests use a transaction that is rolled back after each test.
    
    Returns:
        AsyncClient: An async HTTP client
    """
    # Override database dependency
    async def override_get_db():
        return db_session
    
    original_dependencies = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    
    # Create transport and client
    transport = ASGITransport(app=app)
    
    # Create client with base URL and follow_redirects=True
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True
    ) as client:
        yield client
    
    # Restore original dependencies
    app.dependency_overrides = original_dependencies


@pytest.fixture
def create_payload():
    """
    Create a factory function for generating request payloads.
    
    This fixture provides a function to create standard payloads for
    different API endpoints, ensuring consistency in tests.
    
    Returns:
        callable: A function that generates request payloads
    """
    def _create_payload(payload_type: str, **kwargs) -> Dict[str, Any]:
        """
        Create a request payload of the specified type.
        
        Args:
            payload_type: Type of payload to create (project, version, file, etc.)
            **kwargs: Overrides for default values
        
        Returns:
            Dict[str, Any]: The request payload
        """
        # Default payloads by type
        defaults = {
            "project": {
                "name": "Test Project",
                "description": "A test project created during testing"
            },
            "version": {
                "parent_version_number": 0,
                "name": "Test Version",
                "project_context": "Test project context",
                "change_request": "Add a new feature"
            },
            "file": {
                "path": "src/test_file.tsx",
                "content": "export const TestComponent = () => <div>Test</div>;",
                "operation": "create"
            }
        }
        
        # Get default for the requested type
        payload = defaults.get(payload_type, {}).copy()
        
        # Apply overrides
        payload.update(kwargs)
        
        return payload
    
    return _create_payload