#!/usr/bin/env python
"""
Test for the Model Context Protocol (MCP) server implementation using Supabase REST API.
"""
import os
import uuid
import json
from pprint import pprint

# Import the MCP server implementation using REST API
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
        check_health
        # File operations are handled internally only
    )
    MCP_IMPORTED = True
except ImportError as e:
    print(f"Failed to import MCP server: {e}")
    MCP_IMPORTED = False

# Display environment settings
print("Environment Settings:")
print(f"SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'Not set')}")
print(f"SUPABASE_KEY: {'*****' if os.environ.get('SUPABASE_KEY') else 'Not set'}")
print(f"OPENROUTER_API_KEY: {'*****' if os.environ.get('OPENROUTER_API_KEY') else 'Not set'}")

def run_mcp_tests():
    """Run a series of tests against the MCP server functions."""
    if not MCP_IMPORTED:
        print("❌ Cannot run tests - MCP server module not imported")
        return False
    
    print("\n🔍 Testing MCP with Supabase REST API...")
    
    # Step 1: Check health
    print("\n1. Checking MCP server health...")
    health_result = check_health()
    if not health_result.get("success", False):
        print(f"❌ Health check failed: {health_result.get('error', 'Unknown error')}")
        return False
    print(f"✅ Health check passed: {json.dumps(health_result.get('data', {}), indent=2)}")
    
    # Step 2: List existing projects
    print("\n2. Listing existing projects...")
    list_result = list_projects(limit=5)
    if not list_result.get("success", False):
        print(f"❌ Failed to list projects: {list_result.get('error', 'Unknown error')}")
        return False
    
    projects = list_result.get("data", {}).get("items", [])
    print(f"✅ Found {len(projects)} projects")
    if projects:
        print(f"First project: {projects[0]['name']} (ID: {projects[0]['id']})")
    
    # Step 3: Create a new project
    test_project_name = f"MCP REST Test Project {uuid.uuid4()}"
    print(f"\n3. Creating test project: {test_project_name}")
    
    create_result = create_project(
        name=test_project_name,
        description="Test project created via MCP REST API"
    )
    
    if not create_result.get("success", False):
        print(f"❌ Failed to create project: {create_result.get('error', 'Unknown error')}")
        return False
    
    project_id = create_result.get("data", {}).get("id")
    print(f"✅ Project created with ID: {project_id}")
    
    # Step 4: Get the project
    print(f"\n4. Getting project by ID: {project_id}")
    get_result = get_project(project_id=project_id)
    
    if not get_result.get("success", False):
        print(f"❌ Failed to get project: {get_result.get('error', 'Unknown error')}")
        return False
    
    project = get_result.get("data", {})
    print(f"✅ Retrieved project: {project.get('name')} (Description: {project.get('description')})")
    
    # Step 5: Update the project
    updated_name = f"{test_project_name} - Updated"
    print(f"\n5. Updating project to: {updated_name}")
    update_result = update_project(
        project_id=project_id,
        name=updated_name,
        description="Updated description for testing"
    )
    
    if not update_result.get("success", False):
        print(f"❌ Failed to update project: {update_result.get('error', 'Unknown error')}")
        return False
    
    updated_project = update_result.get("data", {})
    print(f"✅ Project updated: {updated_project.get('name')} (Description: {updated_project.get('description')})")
    
    # Step 6: Create a version
    print("\n6. Creating a new version")
    version_result = create_version(
        project_id=project_id,
        name="Initial version"
    )
    
    if not version_result.get("success", False):
        print(f"❌ Failed to create version: {version_result.get('error', 'Unknown error')}")
        return False
    
    version_id = version_result.get("data", {}).get("id")
    version_number = version_result.get("data", {}).get("version_number")
    print(f"✅ Version created with ID: {version_id} (Version number: {version_number})")
    
    # Step 7: List versions
    print("\n7. Listing versions for the project")
    versions_result = list_versions(project_id=project_id)
    
    if not versions_result.get("success", False):
        print(f"❌ Failed to list versions: {versions_result.get('error', 'Unknown error')}")
        return False
    
    versions = versions_result.get("data", {}).get("items", [])
    print(f"✅ Found {len(versions)} versions")
    
    # Step 8: Delete the project (soft delete)
    print(f"\n8. Cleaning up: Deleting test project {project_id}")
    delete_result = delete_project(project_id=project_id)
    
    if not delete_result.get("success", False):
        print(f"❌ Failed to delete project: {delete_result.get('error', 'Unknown error')}")
        return False
    
    print("✅ Project successfully deleted (soft delete)")
    
    # Final Check: Verify soft deletion worked
    verify_result = get_project(project_id=project_id)
    project_exists = verify_result.get("success", False)
    project_active = verify_result.get("data", {}).get("active", True) if project_exists else False
    
    if project_active:
        print("❌ Project still marked as active after deletion")
        return False
    
    print("\n✅ All MCP REST API tests completed successfully!")
    return True

def main():
    """Run all tests and return success/failure."""
    success = run_mcp_tests()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)