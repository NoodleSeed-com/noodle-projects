"""
Authentication fixtures for tests.

This module provides fixtures for mocking authentication and authorization.
"""
import pytest
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


@pytest.fixture
def mock_oauth_token():
    """
    Create a mock OAuth token for testing.
    
    This fixture creates a mock OAuth2 token that can be used
    for testing authenticated endpoints.
    
    Returns:
        str: A mock OAuth2 token
    """
    return "mock-access-token"


@pytest.fixture
def mock_current_user():
    """
    Create a mock current user for testing.
    
    This fixture creates a mock user that can be used for testing
    authenticated endpoints.
    
    Returns:
        dict: A dictionary representing the current user
    """
    return {
        "id": "mock-user-id",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "roles": ["user"]
    }


@pytest.fixture
def patch_auth_dependency(mock_current_user):
    """
    Patch authentication dependencies.
    
    This fixture patches FastAPI's OAuth2PasswordBearer dependency to return
    a mock token, bypassing actual authentication.
    """
    # Create mock dependency
    async def override_dependency():
        return mock_current_user
    
    # Find all auth dependencies and patch them
    with patch("app.auth.get_current_user", side_effect=override_dependency):
        yield


@pytest.fixture
def mock_admin_user():
    """
    Create a mock admin user for testing.
    
    This fixture creates a mock admin user that can be used for testing
    endpoints that require admin privileges.
    
    Returns:
        dict: A dictionary representing an admin user
    """
    return {
        "id": "mock-admin-id",
        "username": "adminuser",
        "email": "admin@example.com",
        "is_active": True,
        "roles": ["user", "admin"]
    }


@pytest.fixture
def patch_admin_dependency(mock_admin_user):
    """
    Patch admin authentication dependencies.
    
    This fixture patches admin authentication dependencies to return
    a mock admin user, bypassing actual authentication.
    """
    # Create mock dependency
    async def override_dependency():
        return mock_admin_user
    
    # Find all admin auth dependencies and patch them
    with patch("app.auth.get_current_admin_user", side_effect=override_dependency):
        yield