"""
Database fixtures for tests.

This module provides fixtures for database testing, including:
- Fixtures for unit tests with mocked database sessions
- Fixtures for integration tests with real database connections
- Transaction management utilities
"""
import pytest
import pytest_asyncio
import asyncio
import os
from typing import Dict, Any, Callable, Optional, List
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.config import settings


# ========== EVENT LOOP FIXTURES ==========

@pytest.fixture(scope="function")
def event_loop():
    """
    Create a function-scoped event loop for tests.
    
    This prevents the "Task got Future attached to a different loop" error
    that can occur with pytest-asyncio.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    
    loop.close()
    asyncio.set_event_loop(None)


# ========== SUPABASE TEST FIXTURES ==========

@pytest.fixture(scope="function")
def test_mode():
    """
    Set test mode for Supabase tests.
    """
    original_test_mode = settings.TEST_MODE
    settings.TEST_MODE = True
    
    yield
    
    # Restore original setting
    settings.TEST_MODE = original_test_mode


# ========== SUPABASE MOCK FIXTURES ==========

@pytest.fixture
def mock_supabase_client():
    """
    Create a mock Supabase client for unit tests.
    
    This fixture creates a mock for the Supabase client that can be
    used to simulate Supabase operations in unit tests.
    """
    client = MagicMock()
    
    # Mock table methods
    table_mock = MagicMock()
    client.table.return_value = table_mock
    
    # Mock query builders
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.delete.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.order.return_value = table_mock
    table_mock.limit.return_value = table_mock
    table_mock.range.return_value = table_mock
    
    # Mock execution
    execute_result = MagicMock()
    execute_result.data = []
    table_mock.execute.return_value = execute_result
    
    return client


@pytest.fixture
def mock_data_factory():
    """
    Create a factory for test data objects.
    
    This fixture provides a function to create model-like objects
    for testing, with appropriate timestamps and IDs.
    
    Returns:
        callable: A function that creates test data objects
    """
    def _create_object(obj_type, **kwargs):
        """
        Create a data object for testing.
        
        Args:
            obj_type: Type name for the object
            **kwargs: Attributes to set on the object
            
        Returns:
            The created test object
        """
        # Create a basic dict for the object
        obj = kwargs.copy()
        
        # Add ID if not present
        if 'id' not in obj:
            obj['id'] = str(uuid4())
            
        # Add timestamps if not present
        if 'created_at' not in obj:
            obj['created_at'] = datetime.now(timezone.utc).isoformat()
            
        if 'updated_at' not in obj:
            obj['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        return obj
        
    return _create_object