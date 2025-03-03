#!/usr/bin/env python
"""
Model Context Protocol (MCP) server implementation using Supabase REST API.
This version uses the REST API instead of direct database connections for reliability.
"""
import sys
print("mcp_server_rest.py module is being loaded...", file=sys.stderr)
import os
import json
import uuid
import requests
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, root_validator
import asyncio
from datetime import datetime, timezone

# Supabase configuration from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://jsanjojgtyyfpnfqwhgx.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Utility function to create standard response format
def create_response(success: bool, data: Any = None, error: str = None):
    """Create a standardized response format."""
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    return response

class SupabaseRESTClient:
    """Client for interacting with Supabase using the REST API."""
    
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
    
    async def list_projects(self, limit: int = 100, offset: int = 0, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """List all projects with pagination support."""
        # Build query filters
        active_filter = "" if include_inactive else "&active=eq.true"
        
        response = requests.get(
            f"{self.url}/rest/v1/projects?select=*&order=created_at.desc&limit={limit}&offset={offset}{active_filter}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID."""
        response = requests.get(
            f"{self.url}/rest/v1/projects?id=eq.{project_id}&select=*",
            headers=self.headers
        )
        response.raise_for_status()
        projects = response.json()
        return projects[0] if projects else None
    
    async def create_project(self, name: str, description: str) -> Dict[str, Any]:
        """Create a new project."""
        project_data = {
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
            return created_project[0]
        elif isinstance(created_project, dict):
            return created_project
        else:
            # If we can't get data from response, query for the project we just created
            get_response = requests.get(
                f"{self.url}/rest/v1/projects?name=eq.{name}&order=created_at.desc&limit=1",
                headers=self.headers
            )
            get_response.raise_for_status()
            projects = get_response.json()
            if projects and len(projects) > 0:
                return projects[0]
            raise ValueError("Could not retrieve created project")
    
    async def update_project(self, project_id: str, name: str = None, description: str = None) -> Dict[str, Any]:
        """Update a project's attributes and return the updated project."""
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        
        if not update_data:
            # Nothing to update, return current project
            return await self.get_project(project_id)
            
        # For PATCH operations, we need to add updated_at
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Add a special header to get the updated data back directly
        patch_headers = self.headers.copy()
        patch_headers["Prefer"] = "return=representation"
            
        response = requests.patch(
            f"{self.url}/rest/v1/projects?id=eq.{project_id}",
            headers=patch_headers,  # Use headers with return=representation
            json=update_data
        )
        
        # If we got back data, return that directly
        if response.status_code == 200 and response.content:
            try:
                updated_data = response.json()
                if isinstance(updated_data, list) and len(updated_data) > 0:
                    return updated_data[0]
            except:
                pass
        
        # If the PATCH didn't return data or failed, get the project
        if response.status_code not in [200, 204]:
            raise ValueError(f"Failed to update project: {response.text}")
            
        # Get the updated project
        return await self.get_project(project_id)
    
    async def delete_project(self, project_id: str) -> bool:
        """Soft delete a project by ID."""
        # We use soft delete by setting active=false
        update_data = {
            "active": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add a special header to get the updated data back directly
        patch_headers = self.headers.copy()
        patch_headers["Prefer"] = "return=representation"
        
        response = requests.patch(
            f"{self.url}/rest/v1/projects?id=eq.{project_id}",
            headers=patch_headers,
            json=update_data
        )
        
        # Check for success (either 200 or 204)
        return response.status_code in [200, 204]
    
    async def list_versions(self, project_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all versions for a project."""
        response = requests.get(
            f"{self.url}/rest/v1/versions?project_id=eq.{project_id}&select=*&order=version_number.desc&limit={limit}&offset={offset}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get a version by ID."""
        response = requests.get(
            f"{self.url}/rest/v1/versions?id=eq.{version_id}&select=*",
            headers=self.headers
        )
        response.raise_for_status()
        versions = response.json()
        return versions[0] if versions else None
    
    async def create_version(self, project_id: str, version_number: int, name: str, parent_id: str = None) -> Dict[str, Any]:
        """Create a new version for a project."""
        version_data = {
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
            return created_version[0]
        elif isinstance(created_version, dict):
            return created_version
        else:
            # If we can't get data from response, query for the version we just created
            get_response = requests.get(
                f"{self.url}/rest/v1/versions?project_id=eq.{project_id}&version_number=eq.{version_number}&order=created_at.desc&limit=1",
                headers=self.headers
            )
            get_response.raise_for_status()
            versions = get_response.json()
            if versions and len(versions) > 0:
                return versions[0]
            raise ValueError("Could not retrieve created version")
    
    async def get_file(self, version_id: str, path: str) -> Optional[Dict[str, Any]]:
        """Get a file by version ID and path."""
        # URL encode the path to handle special characters
        encoded_path = requests.utils.quote(path)
        response = requests.get(
            f"{self.url}/rest/v1/files?version_id=eq.{version_id}&path=eq.{encoded_path}&select=*",
            headers=self.headers
        )
        response.raise_for_status()
        files = response.json()
        return files[0] if files else None
    
    async def create_or_update_file(self, version_id: str, path: str, content: str) -> Dict[str, Any]:
        """Create or update a file within a version."""
        # First check if file exists
        existing_file = await self.get_file(version_id, path)
        
        if existing_file:
            # Update existing file
            response = requests.patch(
                f"{self.url}/rest/v1/files?id=eq.{existing_file['id']}",
                headers=self.headers,
                json={"content": content, "updated_at": datetime.now(timezone.utc).isoformat()}
            )
            response.raise_for_status()
            return existing_file
        else:
            # Create new file
            file_data = {
                "version_id": version_id,
                "path": path,
                "content": content
            }
            response = requests.post(
                f"{self.url}/rest/v1/files",
                headers=self.headers,
                json=file_data
            )
            response.raise_for_status()
            created_file = response.json()
            
            # Handle both array and object responses
            if isinstance(created_file, list) and len(created_file) > 0:
                return created_file[0]
            elif isinstance(created_file, dict):
                return created_file
            else:
                # Query for the file we just created
                get_response = requests.get(
                    f"{self.url}/rest/v1/files?version_id=eq.{version_id}&path=eq.{requests.utils.quote(path)}&select=*",
                    headers=self.headers
                )
                get_response.raise_for_status()
                files = get_response.json()
                if files and len(files) > 0:
                    return files[0]
                raise ValueError("Could not retrieve created file")

# Initialize the database client
client = SupabaseRESTClient()

# MCP API functions
async def list_projects(limit: int = 100, offset: int = 0, include_inactive: bool = False):
    """List all projects with pagination support."""
    try:
        projects = await client.list_projects(limit=limit, offset=offset, include_inactive=include_inactive)
        total_count = len(projects)  # This is simplified; in a real implementation, you would do a count query
        
        return create_response(
            success=True,
            data={
                "items": projects,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        return create_response(success=False, error=str(e))

async def get_project(project_id: str):
    """Get a project by ID."""
    try:
        project = await client.get_project(project_id=project_id)
        if not project:
            return create_response(success=False, error=f"Project with ID {project_id} not found")
        
        return create_response(success=True, data=project)
    except Exception as e:
        return create_response(success=False, error=str(e))

async def create_project(name: str, description: str = ""):
    """Create a new project."""
    try:
        project = await client.create_project(name=name, description=description)
        return create_response(success=True, data=project)
    except Exception as e:
        return create_response(success=False, error=str(e))

async def update_project(project_id: str, name: str = None, description: str = None):
    """Update a project's attributes."""
    try:
        # Check if project exists
        project = await client.get_project(project_id=project_id)
        if not project:
            return create_response(success=False, error=f"Project with ID {project_id} not found")
        
        # Update the project - returns updated project
        updated_project = await client.update_project(
            project_id=project_id,
            name=name,
            description=description
        )
        
        return create_response(success=True, data=updated_project)
    except Exception as e:
        return create_response(success=False, error=str(e))

async def delete_project(project_id: str):
    """Soft delete a project by ID."""
    try:
        # Check if project exists
        project = await client.get_project(project_id=project_id)
        if not project:
            return create_response(success=False, error=f"Project with ID {project_id} not found")
        
        # Soft delete the project
        success = await client.delete_project(project_id=project_id)
        if success:
            return create_response(success=True)
        else:
            return create_response(success=False, error="Failed to delete project")
    except Exception as e:
        return create_response(success=False, error=str(e))

async def list_versions(project_id: str, limit: int = 100, offset: int = 0):
    """List all versions for a project."""
    try:
        # Check if project exists
        project = await client.get_project(project_id=project_id)
        if not project:
            return create_response(success=False, error=f"Project with ID {project_id} not found")
        
        versions = await client.list_versions(project_id=project_id, limit=limit, offset=offset)
        total_count = len(versions)  # Simplified count
        
        return create_response(
            success=True,
            data={
                "items": versions,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        return create_response(success=False, error=str(e))

async def get_version(version_id: str):
    """Get a version by ID."""
    try:
        version = await client.get_version(version_id=version_id)
        if not version:
            return create_response(success=False, error=f"Version with ID {version_id} not found")
        
        return create_response(success=True, data=version)
    except Exception as e:
        return create_response(success=False, error=str(e))

async def create_version(project_id: str, name: str, parent_id: str = None):
    """Create a new version for a project."""
    try:
        # Check if project exists
        project = await client.get_project(project_id=project_id)
        if not project:
            return create_response(success=False, error=f"Project with ID {project_id} not found")
        
        # Check if parent version exists if provided
        if parent_id:
            parent_version = await client.get_version(version_id=parent_id)
            if not parent_version:
                return create_response(success=False, error=f"Parent version with ID {parent_id} not found")
        
        # Get the next version number
        versions = await client.list_versions(project_id=project_id, limit=1)
        next_version_number = 1
        if versions:
            next_version_number = max([v["version_number"] for v in versions]) + 1
        
        # Create the version
        version = await client.create_version(
            project_id=project_id,
            version_number=next_version_number,
            name=name,
            parent_id=parent_id
        )
        
        return create_response(success=True, data=version)
    except Exception as e:
        return create_response(success=False, error=str(e))

async def get_file(version_id: str, path: str):
    """Get a file by version ID and path."""
    try:
        # Check if version exists
        version = await client.get_version(version_id=version_id)
        if not version:
            return create_response(success=False, error=f"Version with ID {version_id} not found")
        
        file = await client.get_file(version_id=version_id, path=path)
        if not file:
            return create_response(success=False, error=f"File at path '{path}' not found in version {version_id}")
        
        return create_response(success=True, data=file)
    except Exception as e:
        return create_response(success=False, error=str(e))

async def create_or_update_file(version_id: str, path: str, content: str):
    """Create or update a file within a version."""
    try:
        # Check if version exists
        version = await client.get_version(version_id=version_id)
        if not version:
            return create_response(success=False, error=f"Version with ID {version_id} not found")
        
        file = await client.create_or_update_file(version_id=version_id, path=path, content=content)
        return create_response(success=True, data=file)
    except Exception as e:
        return create_response(success=False, error=str(e))

# Standard MCP server functions for testing
async def check_health():
    """Check the health of the MCP server and its backend services."""
    try:
        # Check database connectivity
        projects = await client.list_projects(limit=1)
        
        return create_response(
            success=True,
            data={
                "status": "healthy",
                "database": "connected",
                "services": ["database", "openrouter"]
            }
        )
    except Exception as e:
        return create_response(
            success=False,
            data={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# MCP function map
# These are the functions that will be exposed through the MCP server
FUNCTIONS = {
    "list_projects": list_projects,
    "get_project": get_project, 
    "create_project": create_project,
    "update_project": update_project,
    "delete_project": delete_project,
    "list_versions": list_versions,
    "get_version": get_version,
    "create_version": create_version,
    "get_file": get_file,
    "create_or_update_file": create_or_update_file,
    "check_health": check_health
}

# Define the MCP server object
# This is the object that will be used by the MCP framework
server = {
    "title": "Noodle Projects API",
    "description": "REST API for managing projects, versions, and files using Supabase backend",
    "version": "1.0.0",
    "functions": FUNCTIONS,
    # Add schema information to make Claude Desktop usage easier
    "schemas": {
        "list_projects": {
            "limit": {"type": "integer", "description": "Maximum number of projects to return", "default": 100},
            "offset": {"type": "integer", "description": "Number of projects to skip (for pagination)", "default": 0},
            "include_inactive": {"type": "boolean", "description": "Whether to include inactive/deleted projects", "default": False}
        },
        "get_project": {
            "project_id": {"type": "string", "description": "UUID of the project", "required": True}
        },
        "create_project": {
            "name": {"type": "string", "description": "Name of the project", "required": True},
            "description": {"type": "string", "description": "Description of the project", "default": ""}
        },
        "update_project": {
            "project_id": {"type": "string", "description": "UUID of the project", "required": True},
            "name": {"type": "string", "description": "New name for the project"},
            "description": {"type": "string", "description": "New description for the project"}
        },
        "delete_project": {
            "project_id": {"type": "string", "description": "UUID of the project", "required": True}
        },
        "list_versions": {
            "project_id": {"type": "string", "description": "UUID of the project", "required": True},
            "limit": {"type": "integer", "description": "Maximum number of versions to return", "default": 100},
            "offset": {"type": "integer", "description": "Number of versions to skip (for pagination)", "default": 0}
        },
        "get_version": {
            "version_id": {"type": "string", "description": "UUID of the version", "required": True}
        },
        "create_version": {
            "project_id": {"type": "string", "description": "UUID of the project", "required": True},
            "name": {"type": "string", "description": "Name of the version", "required": True},
            "parent_id": {"type": "string", "description": "UUID of the parent version (if this is a child version)"}
        },
        "get_file": {
            "version_id": {"type": "string", "description": "UUID of the version", "required": True},
            "path": {"type": "string", "description": "File path within the version", "required": True}
        },
        "create_or_update_file": {
            "version_id": {"type": "string", "description": "UUID of the version", "required": True},
            "path": {"type": "string", "description": "File path within the version", "required": True},
            "content": {"type": "string", "description": "Content of the file", "required": True}
        },
        "check_health": {}
    }
}

# This function is required for MCP to run the server
def run():
    import sys
    print("MCP Server starting...", file=sys.stderr)
    print(f"SERVER OBJECT: {server}", file=sys.stderr)
    return server

# This allows for testing outside of the MCP server
if __name__ == "__main__":
    async def test_mcp():
        """Run some basic tests on the MCP functions."""
        # Test project creation and retrieval
        project_name = f"Test Project {uuid.uuid4()}"
        print(f"Creating project: {project_name}")
        
        create_result = await create_project(name=project_name, description="Test project from MCP REST API")
        if not create_result["success"]:
            print(f"Error creating project: {create_result['error']}")
            return False
        
        project_id = create_result["data"]["id"]
        print(f"Project created with ID: {project_id}")
        
        # Test version creation
        version_result = await create_version(project_id=project_id, name="Initial version")
        if not version_result["success"]:
            print(f"Error creating version: {version_result['error']}")
            return False
        
        version_id = version_result["data"]["id"]
        print(f"Version created with ID: {version_id}")
        
        # Test file creation
        file_path = "src/main.js"
        file_content = "console.log('Hello from MCP!');"
        file_result = await create_or_update_file(
            version_id=version_id,
            path=file_path,
            content=file_content
        )
        if not file_result["success"]:
            print(f"Error creating file: {file_result['error']}")
            return False
        
        print(f"File created at path: {file_path}")
        
        # Test file retrieval
        get_file_result = await get_file(version_id=version_id, path=file_path)
        if not get_file_result["success"]:
            print(f"Error retrieving file: {get_file_result['error']}")
            return False
        
        retrieved_content = get_file_result["data"]["content"]
        print(f"Retrieved file content: {retrieved_content}")
        
        # Verify content
        if retrieved_content != file_content:
            print(f"Error: Retrieved content doesn't match original content!")
            return False
        
        print("All tests passed!")
        return True
    
    # Run the test
    success = asyncio.run(test_mcp())
    exit(0 if success else 1)