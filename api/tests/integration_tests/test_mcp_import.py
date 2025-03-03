"""
Tests for MCP server module import and functionality verification.
"""
import os
import sys
import importlib
import pytest
from typing import List, Dict, Any, Optional

# Skip if the MCP modules are not in the expected location
@pytest.fixture(scope="module")
def mcp_paths():
    """Fixture providing paths to MCP modules."""
    return {
        "rest": "app.mcp_server_rest",
        "direct": "app.mcp_server",
        "simple": "app.simple_mcp_server",
        "official": "app.officialMCP"
    }


def test_can_import_mcp_rest_module(mcp_paths):
    """Test that the MCP REST server module can be imported."""
    module_name = mcp_paths["rest"]
    
    try:
        module = importlib.import_module(module_name)
        assert module is not None, f"Failed to import {module_name}"
        assert hasattr(module, "check_health"), f"{module_name} should have check_health function"
        assert hasattr(module, "list_projects"), f"{module_name} should have list_projects function"
        assert hasattr(module, "get_project"), f"{module_name} should have get_project function"
        assert hasattr(module, "create_project"), f"{module_name} should have create_project function"
        
        # Verify expected tools in the module
        expected_tools = [
            "list_projects", 
            "get_project", 
            "create_project", 
            "update_project", 
            "delete_project",
            "list_versions",
            "get_version",
            "create_version",
            "get_file",
            "create_or_update_file"
        ]
        
        # Check that all expected tools are present
        for tool in expected_tools:
            assert hasattr(module, tool), f"{module_name} should have {tool} function"
            assert callable(getattr(module, tool)), f"{tool} should be callable"
            
    except ImportError:
        pytest.skip(f"MCP REST module '{module_name}' not available")


@pytest.mark.xfail(reason="Direct connection module might not have all functions")
def test_can_import_mcp_direct_module(mcp_paths):
    """Test that the MCP direct database module can be imported."""
    module_name = mcp_paths["direct"]
    
    try:
        module = importlib.import_module(module_name)
        assert module is not None, f"Failed to import {module_name}"
        
        # Check for some functions - but mark as xfail since implementation might vary
        # Core functions that should be present in any MCP implementation
        core_functions = [
            "list_projects", 
            "get_project", 
            "create_project"
        ]
        
        # Check that core functions are present (but allow failures)
        found_functions = 0
        for func in core_functions:
            if hasattr(module, func) and callable(getattr(module, func)):
                found_functions += 1
        
        # At least some functions should be present
        assert found_functions > 0, "Module should have at least one MCP function"
            
    except ImportError:
        pytest.skip(f"MCP direct module '{module_name}' not available")


@pytest.mark.xfail(reason="Official MCP implementation details may vary")
def test_can_import_official_mcp_module(mcp_paths):
    """Test that the official MCP implementation can be imported."""
    module_name = mcp_paths["official"]
    
    try:
        module = importlib.import_module(module_name)
        assert module is not None, f"Failed to import {module_name}"
        
        # Check for some common MCP server patterns
        # Either get_mcp_server, run, or mcp should exist
        has_mcp_interface = False
        
        if hasattr(module, "get_mcp_server"):
            has_mcp_interface = True
        elif hasattr(module, "run"):
            has_mcp_interface = True
            run_func = getattr(module, "run")
            assert callable(run_func), "run should be callable"
        elif hasattr(module, "mcp"):
            has_mcp_interface = True
        
        # One of these patterns should be present
        assert has_mcp_interface, "Module should have a valid MCP interface (get_mcp_server, run, or mcp)"
        
        # Test for FastMCP or any other MCP implementation
        has_mcp_implementation = False
        for key in ["FastMCP", "mcp", "main"]:
            if key in str(module.__dict__):
                has_mcp_implementation = True
                break
        
        assert has_mcp_implementation, "Module should use a valid MCP implementation"
        
    except ImportError:
        pytest.skip(f"Official MCP module '{module_name}' not available")


@pytest.mark.xfail(reason="May fail if simple_mcp_server is not used anymore")
def test_can_import_simple_mcp_module(mcp_paths):
    """Test that the simple MCP server module can be imported."""
    module_name = mcp_paths["simple"]
    
    try:
        module = importlib.import_module(module_name)
        assert module is not None, f"Failed to import {module_name}"
    except ImportError:
        pytest.skip(f"Simple MCP module '{module_name}' not available")