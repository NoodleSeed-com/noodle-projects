"""
Synchronous MCP server implementation using the official Supabase client.
"""
import logging
import os
from typing import Dict, Any, Optional, Union
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from app.errors import ErrorType
from app.services.supabase.client import SupabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncMCP:
    """MCP server implementation for Noodle Projects using synchronous Supabase client."""
    
    def __init__(self, name: str = "NoodleProjects"):
        """Initialize the synchronous MCP server.
        
        Args:
            name: Name of the MCP server
        """
        self.name = name
        self.service = SupabaseService()
        self.mcp = FastMCP(name)
        self._register_tools()
        
        logger.info(f"SyncMCP initialized with Supabase client")
    
    def _register_tools(self):
        """Register tools with the MCP server."""
        # Project tools
        self.mcp.tool()(self.list_projects)
        self.mcp.tool()(self.get_project)
        self.mcp.tool()(self.create_project)
        self.mcp.tool()(self.update_project)
        self.mcp.tool()(self.delete_project)
        
        # Version tools
        self.mcp.tool()(self.list_versions)
        self.mcp.tool()(self.get_version)
        self.mcp.tool()(self.create_version)
        
        
        # Health check
        self.mcp.tool()(self.check_health)
    
    def list_projects(
        self,
        skip: Optional[int] = 0,
        limit: Optional[int] = 100,
        include_inactive: Optional[bool] = False
    ) -> Dict[str, Any]:
        """List all projects with pagination.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive (deleted) projects
            
        Returns:
            List of projects with pagination info
        """
        return self.service.list_projects(
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
    
    def get_project(
        self,
        project_id: UUID
    ) -> Dict[str, Any]:
        """Get project details by ID.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Project details
        """
        return self.service.get_project(project_id=project_id)
    
    def create_project(
        self,
        name: str,
        description: Optional[str] = ""
    ) -> Dict[str, Any]:
        """Create a new project.
        
        Args:
            name: Project name
            description: Optional project description
            
        Returns:
            Created project details
        """
        return self.service.create_project(
            name=name,
            description=description
        )
    
    def update_project(
        self,
        project_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing project.
        
        Args:
            project_id: UUID of the project to update
            name: Optional new project name
            description: Optional new project description
            is_active: Optional new project active status
            
        Returns:
            Updated project details
        """
        return self.service.update_project(
            project_id=project_id,
            name=name,
            description=description,
            is_active=is_active
        )
    
    def delete_project(
        self,
        project_id: UUID
    ) -> Dict[str, Any]:
        """Soft-delete a project by setting is_active to false.
        
        Args:
            project_id: UUID of the project to delete
            
        Returns:
            Success status
        """
        return self.service.delete_project(project_id=project_id)
    
    def list_versions(
        self,
        project_id: UUID,
        skip: Optional[int] = 0,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """List all versions of a project.
        
        Args:
            project_id: UUID of the project
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of project versions with pagination info
        """
        return self.service.list_versions(
            project_id=project_id,
            skip=skip,
            limit=limit
        )
    
    def get_version(
        self,
        project_id: UUID,
        version_number: int,
        include_files: Optional[bool] = True
    ) -> Dict[str, Any]:
        """Get version details by project ID and version number.
        
        Args:
            project_id: UUID of the project
            version_number: Version number
            include_files: Whether to include files in the response
            
        Returns:
            Version details with optional files
        """
        return self.service.get_version(
            project_id=project_id,
            version_number=version_number,
            include_files=include_files
        )
    
    def create_version(
        self,
        project_id: UUID,
        name: str,
        parent_version_number: int,
        project_context: str,
        change_request: str
    ) -> Dict[str, Any]:
        """Create a new version for a project.
        
        Args:
            project_id: UUID of the project
            name: Name for the new version
            parent_version_number: Version number of the parent version
            project_context: Context about the project
            change_request: Description of changes requested
            
        Returns:
            Created version details with files
        """
        return self.service.create_version(
            project_id=project_id,
            name=name,
            parent_version_number=parent_version_number,
            project_context=project_context,
            change_request=change_request
        )
    
    
    def check_health(self) -> Dict[str, Any]:
        """Check the health of the MCP server and its backend services.
        
        Returns:
            Health status information
        """
        return self.service.check_health()
    
    def get_server_definition(self) -> Dict[str, Any]:
        """Get the MCP server definition for REST API use."""
        return {
            "title": f"{self.name} API",
            "description": "API for managing projects, versions, and files using Supabase",
            "version": "1.0.0",
            "functions": {
                "list_projects": self.list_projects,
                "get_project": self.get_project,
                "create_project": self.create_project,
                "update_project": self.update_project,
                "delete_project": self.delete_project,
                "list_versions": self.list_versions,
                "get_version": self.get_version,
                "create_version": self.create_version,
                "check_health": self.check_health
                # File operations are handled internally only
            },
            # Add schema information to make Claude Desktop usage easier
            "schemas": {
                "list_projects": {
                    "limit": {"type": "integer", "description": "Maximum number of projects to return", "default": 100},
                    "skip": {"type": "integer", "description": "Number of projects to skip (for pagination)", "default": 0},
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
                    "description": {"type": "string", "description": "New description for the project"},
                    "is_active": {"type": "boolean", "description": "New active status for the project"}
                },
                "delete_project": {
                    "project_id": {"type": "string", "description": "UUID of the project", "required": True}
                },
                "list_versions": {
                    "project_id": {"type": "string", "description": "UUID of the project", "required": True},
                    "limit": {"type": "integer", "description": "Maximum number of versions to return", "default": 100},
                    "skip": {"type": "integer", "description": "Number of versions to skip (for pagination)", "default": 0}
                },
                "get_version": {
                    "project_id": {"type": "string", "description": "UUID of the project", "required": True},
                    "version_number": {"type": "integer", "description": "Version number", "required": True},
                    "include_files": {"type": "boolean", "description": "Whether to include files in the response", "default": True}
                },
                "create_version": {
                    "project_id": {"type": "string", "description": "UUID of the project", "required": True},
                    "name": {"type": "string", "description": "Name of the version", "required": True},
                    "parent_version_number": {"type": "integer", "description": "Version number of the parent version", "required": True},
                    "project_context": {"type": "string", "description": "Context about the project for AI", "required": True},
                    "change_request": {"type": "string", "description": "Description of changes requested", "required": True}
                },
                "check_health": {}
            }
        }
    
    def run(self):
        """Run the MCP server."""
        self.mcp.run()

# Create a default MCP server instance
default_mcp = SyncMCP()

# MCP server run function for module-level use
def run():
    """Run the MCP server and return server definition for REST API."""
    logger.info(f"Starting Noodle SyncMCP server")
    mcp_server = SyncMCP()
    return mcp_server.get_server_definition()

if __name__ == "__main__":
    """Run the MCP server directly."""
    default_mcp.run()