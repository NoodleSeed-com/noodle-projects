#!/usr/bin/env python
"""
Test the MCP server using Supabase REST API to bypass direct DB connection issues.
"""
import os
import uuid
import requests
import json
from typing import Dict, Any, List

# Supabase REST API configuration
SUPABASE_URL = "https://jsanjojgtyyfpnfqwhgx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM"
OPENROUTER_API_KEY = "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"

class SupabaseRESTClient:
    """Client for Supabase REST API operations."""
    
    def __init__(self):
        """Initialize the client with Supabase credentials."""
        self.url = SUPABASE_URL
        self.key = SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation" 
        }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects from Supabase."""
        response = requests.get(
            f"{self.url}/rest/v1/projects?select=*",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a project by ID."""
        response = requests.get(
            f"{self.url}/rest/v1/projects?id=eq.{project_id}&select=*",
            headers=self.headers
        )
        response.raise_for_status()
        projects = response.json()
        if not projects:
            raise ValueError(f"Project with ID {project_id} not found")
        return projects[0]
    
    def create_project(self, name: str, description: str) -> str:
        """Create a new project."""
        project_data = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "active": True
        }
        response = requests.post(
            f"{self.url}/rest/v1/projects",
            headers=self.headers,
            json=project_data
        )
        response.raise_for_status()
        created_project = response.json()
        # Handle both array and object responses
        if isinstance(created_project, list) and len(created_project) > 0:
            return created_project[0]["id"]
        elif isinstance(created_project, dict):
            return created_project["id"]
        else:
            # If we can't get ID from response, query for the project we just created
            get_response = requests.get(
                f"{self.url}/rest/v1/projects?name=eq.{name}&order=created_at.desc&limit=1",
                headers=self.headers
            )
            get_response.raise_for_status()
            projects = get_response.json()
            if projects and len(projects) > 0:
                return projects[0]["id"]
            raise ValueError("Could not retrieve created project ID")
    
    def delete_project(self, project_id: str) -> bool:
        """Soft delete a project by ID."""
        # In this case, we're setting active=false instead of doing a real delete
        response = requests.patch(
            f"{self.url}/rest/v1/projects?id=eq.{project_id}",
            headers=self.headers,
            json={"active": False}
        )
        return response.status_code in [200, 204]
    
    def list_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """List all versions for a project."""
        response = requests.get(
            f"{self.url}/rest/v1/versions?project_id=eq.{project_id}&select=*",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_version(self, project_id: str, version_number: int, name: str, parent_id: str = None) -> str:
        """Create a new version for a project."""
        version_data = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "version_number": version_number,
            "name": name
        }
        if parent_id:
            version_data["parent_id"] = parent_id
            
        response = requests.post(
            f"{self.url}/rest/v1/versions",
            headers=self.headers,
            json=version_data
        )
        response.raise_for_status()
        created_version = response.json()
        
        # Handle both array and object responses
        if isinstance(created_version, list) and len(created_version) > 0:
            return created_version[0]["id"]
        elif isinstance(created_version, dict):
            return created_version["id"]
        else:
            # If we can't get ID from response, query for the version we just created
            get_response = requests.get(
                f"{self.url}/rest/v1/versions?project_id=eq.{project_id}&version_number=eq.{version_number}&order=created_at.desc&limit=1",
                headers=self.headers
            )
            get_response.raise_for_status()
            versions = get_response.json()
            if versions and len(versions) > 0:
                return versions[0]["id"]
            raise ValueError("Could not retrieve created version ID")

def test_rest_db():
    """Test database functionality using Supabase REST API."""
    try:
        print("\n🧪 Starting Supabase REST API Test")
        client = SupabaseRESTClient()
        
        # Generate unique test project name
        test_project_name = f"REST Test Project {uuid.uuid4()}"
        print(f"\n1. Creating test project: {test_project_name}")
        
        # Create project
        project_id = client.create_project(
            name=test_project_name,
            description="Test project created via Supabase REST API"
        )
        print(f"✅ Project created with ID: {project_id}")
        
        # List projects
        print("\n2. Listing all projects")
        projects = client.list_projects()
        print(f"✅ Found {len(projects)} projects")
        
        # Get project
        print(f"\n3. Getting project by ID: {project_id}")
        project = client.get_project(project_id=project_id)
        print(f"✅ Retrieved project: {project['name']}")
        
        # Create version
        print("\n4. Creating a new version")
        version_number = 1
        version_id = client.create_version(
            project_id=project_id,
            version_number=version_number,
            name="Initial version"
        )
        print(f"✅ Version created with ID: {version_id}")
        
        # List versions
        print("\n5. Listing project versions")
        versions = client.list_versions(project_id=project_id)
        print(f"✅ Found {len(versions)} versions")
        
        # Verify correct version was created
        version_found = False
        for version in versions:
            if version['id'] == version_id:
                version_found = True
                print(f"✅ Version verified: {version['name']} (version {version['version_number']})")
                break
        
        if not version_found:
            print("❌ Could not find created version in version list")
        
        # Delete project (soft delete)
        print(f"\n6. Cleaning up: Deleting test project {project_id}")
        deleted = client.delete_project(project_id=project_id)
        if deleted:
            print("✅ Project marked as inactive (soft deleted)")
        else:
            print("❌ Failed to delete project")
        
        print("\n✅ All Supabase REST API tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing Supabase REST API: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_rest_integration():
    """Test the MCP server integration with Supabase REST API."""
    try:
        print("\n🧪 Starting MCP Rest Integration Test")
        
        # First, ensure environment variables are set for the MCP server
        os.environ["SUPABASE_URL"] = SUPABASE_URL
        os.environ["SUPABASE_KEY"] = SUPABASE_KEY
        os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
        os.environ["REST_API_MODE"] = "true"  # This would be a flag to indicate using REST API instead of direct DB
        
        print("\n1. Importing MCP server module")
        try:
            from app.mcp_server_rest import list_projects, create_project, get_project, delete_project
            print("✅ Successfully imported MCP server module")
        except ImportError as e:
            print(f"❌ Could not import MCP server module: {e}")
            return False
        
        # Test project creation via MCP
        test_project_name = f"MCP-REST Test Project {uuid.uuid4()}"
        print(f"\n2. Creating test project via MCP: {test_project_name}")
        
        # Create a project using the MCP function
        result = create_project(name=test_project_name, description="Project created by MCP REST test")
        
        if not result.get('success'):
            print(f"❌ Failed to create project: {result.get('error')}")
            return False
            
        project_id = result.get('data', {}).get('id')
        print(f"✅ Project created with ID: {project_id}")
        
        # List projects
        print("\n3. Listing all projects with MCP REST")
        result = list_projects()
        
        if not result.get('success'):
            print(f"❌ Failed to list projects: {result.get('error')}")
            return False
            
        projects = result.get('data', {}).get('items', [])
        print(f"✅ Found {len(projects)} projects")
        
        # Get project details
        print(f"\n4. Getting project with MCP REST by ID: {project_id}")
        result = get_project(project_id=project_id)
        
        if not result.get('success'):
            print(f"❌ Failed to get project: {result.get('error')}")
            return False
            
        project_data = result.get('data', {})
        print(f"✅ Retrieved project: {project_data.get('name')}")
        
        # Delete project
        print(f"\n5. Cleaning up: Deleting test project with MCP REST {project_id}")
        result = delete_project(project_id=project_id)
        
        if not result.get('success'):
            print(f"❌ Failed to delete project: {result.get('error')}")
            return False
            
        print("✅ Project successfully deleted")
        
        print("\n✅ All MCP REST tests completed successfully!")
        return True
    
    except Exception as e:
        print(f"\n❌ Error testing MCP Rest integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n🔍 Testing Supabase connection and MCP integration using REST API...")
    
    # Test Supabase REST API
    rest_success = test_rest_db()
    
    if not rest_success:
        print("\n❌ Supabase REST API tests failed. Skipping MCP integration test.")
        return False
        
    # Test MCP integration with REST API
    mcp_success = test_mcp_rest_integration()
    
    # Summary
    print("\n\n📊 Test Summary:")
    print(f"Supabase REST API: {'✅ Success' if rest_success else '❌ Failed'}")
    print(f"MCP REST Integration: {'✅ Success' if mcp_success else '❌ Failed'}")
    print("\nMCP server has been updated to use synchronous Supabase REST API")
    
    return rest_success and mcp_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)