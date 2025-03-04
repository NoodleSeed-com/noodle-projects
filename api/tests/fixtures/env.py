"""
Environment fixtures for tests.

This module provides fixtures for managing environment variables during tests.
"""
import os
import pytest
from typing import Dict, Any, Optional


@pytest.fixture(scope="session")
def environment_variables():
    """
    Store and restore environment variables for the test session.
    
    This fixture saves the original environment at the beginning of the test session
    and restores it at the end, ensuring tests don't have side effects on the environment.
    
    Returns:
        callable: A function that can be used to temporarily set environment variables.
    """
    # Store original environment
    original_env = os.environ.copy()
    
    # Create a function to safely set environment variables temporarily
    def _set_env_vars(variables: Dict[str, Any], clear_existing: bool = False):
        """
        Set environment variables temporarily for a test.
        
        Args:
            variables: Dictionary of environment variables to set
            clear_existing: If True, clear all existing env vars first
        """
        if clear_existing:
            for key in list(os.environ.keys()):
                del os.environ[key]
                
        # Set new variables
        for key, value in variables.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = str(value)
    
    yield _set_env_vars
    
    # Restore original environment after all tests
    for key in list(os.environ.keys()):
        if key not in original_env:
            del os.environ[key]
        else:
            os.environ[key] = original_env[key]


@pytest.fixture
def mock_env(monkeypatch):
    """
    Create a fixture that mocks environment variables safely.
    
    This fixture allows setting environment variables for a single test
    without modifying the actual environment. It uses pytest's monkeypatch
    to safely handle environment variables.
    
    Args:
        monkeypatch: pytest's monkeypatch fixture
        
    Returns:
        callable: A function that sets environment variables safely
    """
    def _set_env(name: str, value: Optional[str] = None):
        """
        Set an environment variable for the duration of a test.
        
        Args:
            name: Environment variable name
            value: Value to set (None to unset)
        """
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    
    return _set_env


@pytest.fixture
def test_mode(mock_env):
    """
    Set the application to test mode.
    
    This fixture ensures the TEST_MODE environment variable is set,
    which puts the application into test mode.
    """
    mock_env("TEST_MODE", "True")
    yield


@pytest.fixture
def mock_supabase_credentials(mock_env):
    """
    Set mock Supabase credentials for testing.
    
    This fixture creates test credentials for Supabase tests
    that don't need to access the real Supabase instance.
    """
    mock_env("SUPABASE_URL", "https://test-project.supabase.co")
    mock_env("SUPABASE_KEY", "test-key-not-real")
    yield