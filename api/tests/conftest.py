"""
Root conftest.py file that imports and makes available all the fixtures.

This file imports fixtures from the fixtures/ directory,
making them available to all tests without having to import them explicitly.
"""
import os
import pytest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all fixtures so they're available to all tests
from api.tests.fixtures.env import (
    environment_variables,
    mock_env,
    test_mode,
    mock_supabase_credentials
)

from api.tests.fixtures.db import (
    event_loop,
    test_mode,
    mock_supabase_client,
    mock_data_factory
)

from api.tests.fixtures.fs import (
    temp_dir,
    temp_file,
    temp_template_dir
)

from api.tests.fixtures.mocks import (
    mock_openrouter_service,
    patch_openrouter_service,
    mock_supabase_service,
    patch_supabase_service
)

from api.tests.fixtures.auth import (
    mock_oauth_token,
    mock_current_user,
    patch_auth_dependency,
    mock_admin_user,
    patch_admin_dependency
)

from api.tests.fixtures.client import (
    client,
    async_client,
    create_payload
)

from api.tests.fixtures.validators import (
    validate_response,
    validate_paginated_response,
    schema_validators
)


# Define test environments for conditional test execution
def pytest_configure(config):
    """Add test environment markers."""
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "requires_supabase: mark a test as requiring Supabase")
    

# Skip tests that require Supabase if credentials are not available
def pytest_runtest_setup(item):
    """Skip tests that require external services if credentials are not available."""
    # Check for Supabase tests
    if "requires_supabase" in [mark.name for mark in item.iter_markers()]:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            pytest.skip("Test requires Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY environment variables.")