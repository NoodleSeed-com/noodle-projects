#!/usr/bin/env python
"""
Test the MCP server locally by verifying it imports correctly and 
has the expected tools defined.
"""
import sys
import os
import importlib.util
import logging

def test_mcp_server():
    """Test the MCP server by directly importing the module."""
    print("Testing MCP server...")
    
    # Set PYTHONPATH to include the parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    print(f"Setting PYTHONPATH to include: {parent_dir}")
    
    # Try to import the module directly to check for import errors
    try:
        # First, check if we can import the app module
        print("Checking if app module can be imported...")
        sys.path.insert(0, parent_dir)
        import app
        print("✅ Successfully imported app module")
        
        # Now check if we can import the mcp_server module
        print("Checking if app.mcp_server module can be imported...")
        try:
            from app import mcp_server
            print("✅ Successfully imported mcp_server module")
            
            # Check for key components in the module
            print("\nVerifying MCP server components...")
            if hasattr(mcp_server, 'mcp'):
                # Get the tools that are decorated with @mcp.tool()
                # This is more accurate than just looking at all callables
                tools = []
                for name, func in vars(mcp_server).items():
                    if callable(func) and hasattr(func, '__module__') and func.__module__ == 'app.mcp_server':
                        # Check if this is an actual tool function and not a helper or imported function
                        if name in ['list_projects', 'get_project', 'create_project', 'update_project', 
                                   'delete_project', 'list_versions', 'get_version', 'create_version']:
                            tools.append(name)
                print(f"✅ Found MCP server instance with {len(tools)} tools:")
                
                # Expected tools
                expected_tools = [
                    "list_projects", 
                    "get_project", 
                    "create_project", 
                    "update_project", 
                    "delete_project",
                    "list_versions",
                    "get_version",
                    "create_version"
                ]
                
                # Check each expected tool
                all_tools_found = True
                for expected_tool in expected_tools:
                    if expected_tool in tools:
                        print(f"  ✅ Found tool: {expected_tool}")
                    else:
                        print(f"  ❌ Missing tool: {expected_tool}")
                        all_tools_found = False
                
                # Additional tools (not in expected list)
                for tool in tools:
                    if tool not in expected_tools:
                        print(f"  ℹ️ Additional tool: {tool}")
                
                if all_tools_found:
                    print("\n✅ MCP server is configured correctly with all expected tools!")
                    return True
                else:
                    print("\n❌ MCP server is missing some expected tools.")
                    return False
            else:
                print("❌ Could not find 'mcp' FastMCP instance in the module")
                return False
            
        except ImportError as e:
            print(f"❌ Failed to import mcp_server module: {e}")
            return False
        
    except ImportError as e:
        print(f"❌ Failed to import app module: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_mcp_server()