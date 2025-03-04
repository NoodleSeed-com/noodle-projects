"""
Supabase client implementation using the official supabase-py client.
"""
import os
import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from uuid import UUID

from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Log warning if credentials are not set
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("SUPABASE_URL or SUPABASE_KEY environment variables are not set. Supabase client will not function properly.")

# Singleton client instance
_supabase_client = None

def get_supabase_client() -> Client:
    """
    Get the Supabase client instance.
    Returns a singleton instance of the Supabase client.
    
    Returns:
        Client: The Supabase client instance
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY environment variables are not set
    """
    global _supabase_client
    
    if _supabase_client is None:
        # Validate credentials
        if not SUPABASE_URL or not SUPABASE_KEY:
            error_msg = "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            logger.info("Initializing Supabase client...")
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    return _supabase_client

class SupabaseService:
    """
    Service for interacting with Supabase database tables.
    All operations are synchronous.
    """
    
    def __init__(self):
        """Initialize the Supabase service."""
        self.client = get_supabase_client()
    
    def list_projects(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> Dict[str, Any]:
        """
        List all projects with pagination.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive (deleted) projects
            
        Returns:
            Dictionary with project data
        """
        try:
            query = self.client.table("projects").select("*").order("created_at", desc=True)
            
            if not include_inactive:
                query = query.eq("active", True)
            
            response = query.range(skip, skip + limit - 1).execute()
            
            return {
                "success": True,
                "data": {
                    "total": len(response.data),  # This is a simplified count
                    "items": response.data,
                    "skip": skip,
                    "limit": limit
                }
            }
        except Exception as e:
            logger.error(f"Error in list_projects: {e}")
            return {"success": False, "error": str(e)}
    
    def get_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """
        Get a project by ID.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Dictionary with project data or error
        """
        try:
            response = self.client.table("projects").select("*").eq("id", str(project_id)).execute()
            
            if not response.data:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": "NOT_FOUND"
                }
                
            return {
                "success": True,
                "data": response.data[0]
            }
        except Exception as e:
            logger.error(f"Error in get_project: {e}")
            return {"success": False, "error": str(e)}
    
    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Optional project description
            
        Returns:
            Dictionary with created project data or error
        """
        try:
            project_data = {
                "id": str(uuid.uuid4()),
                "name": name,
                "description": description,
                "active": True
            }
            
            response = self.client.table("projects").insert(project_data).execute()
            
            if not response.data:
                return {"success": False, "error": "Failed to create project"}
                
            return {"success": True, "data": response.data[0]}
        except Exception as e:
            logger.error(f"Error in create_project: {e}")
            return {"success": False, "error": str(e)}
    
    def update_project(
        self, 
        project_id: Union[str, UUID], 
        name: Optional[str] = None, 
        description: Optional[str] = None, 
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update a project.
        
        Args:
            project_id: UUID of the project
            name: Optional new project name
            description: Optional new project description
            is_active: Optional new project active status
            
        Returns:
            Dictionary with updated project data or error
        """
        try:
            # Check if project exists
            project_response = self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            # Build update data
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if is_active is not None:
                update_data["active"] = is_active
            
            if not update_data:
                # Nothing to update, return current project
                return project_response
                
            # Update project
            response = self.client.table("projects").update(update_data).eq("id", str(project_id)).execute()
            
            if not response.data:
                return {"success": False, "error": "Failed to update project"}
                
            return {"success": True, "data": response.data[0]}
        except Exception as e:
            logger.error(f"Error in update_project: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """
        Soft-delete a project by setting is_active to false.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Dictionary with operation status and data
        """
        try:
            # Use update method to soft-delete
            return self.update_project(project_id, is_active=False)
        except Exception as e:
            logger.error(f"Error in delete_project: {e}")
            return {"success": False, "error": str(e)}
    
    def list_versions(
        self, 
        project_id: Union[str, UUID], 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List all versions for a project.
        
        Args:
            project_id: UUID of the project
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with version data
        """
        try:
            # Check if project exists and is active
            project_response = self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            # Only list versions for active projects
            if not project_response["data"]["active"]:
                return {
                    "success": True,
                    "data": {
                        "total": 0,
                        "items": [],
                        "skip": skip,
                        "limit": limit
                    }
                }
            
            # Get versions
            response = self.client.table("versions") \
                .select("*") \
                .eq("project_id", str(project_id)) \
                .order("version_number", desc=True) \
                .range(skip, skip + limit - 1) \
                .execute()
            
            return {
                "success": True,
                "data": {
                    "total": len(response.data),
                    "items": response.data,
                    "skip": skip,
                    "limit": limit
                }
            }
        except Exception as e:
            logger.error(f"Error in list_versions: {e}")
            return {"success": False, "error": str(e)}
    
    def get_version(
        self, 
        project_id: Union[str, UUID], 
        version_number: int, 
        include_files: bool = True
    ) -> Dict[str, Any]:
        """
        Get a version by project ID and version number.
        
        Args:
            project_id: UUID of the project
            version_number: Version number
            include_files: Whether to include files in the response
            
        Returns:
            Dictionary with version data or error
        """
        try:
            # Check if project exists
            project_response = self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            # Get the version
            response = self.client.table("versions") \
                .select("*") \
                .eq("project_id", str(project_id)) \
                .eq("version_number", version_number) \
                .execute()
            
            if not response.data:
                return {
                    "success": False,
                    "error": f"Version {version_number} not found for project {project_id}",
                    "error_type": "NOT_FOUND"
                }
            
            version = response.data[0]
            
            # Include files if requested
            if include_files:
                files_response = self.client.table("files") \
                    .select("*") \
                    .eq("version_id", version["id"]) \
                    .execute()
                
                # Add files to version data
                version["files"] = files_response.data
            
            return {
                "success": True,
                "data": version
            }
        except Exception as e:
            logger.error(f"Error in get_version: {e}")
            return {"success": False, "error": str(e)}
    
    def get_file(self, version_id: Union[str, UUID], path: str) -> Dict[str, Any]:
        """
        Get a file by version ID and path.
        
        Args:
            version_id: UUID of the version
            path: File path
            
        Returns:
            Dictionary with file data or error
        """
        try:
            response = self.client.table("files") \
                .select("*") \
                .eq("version_id", str(version_id)) \
                .eq("path", path) \
                .execute()
            
            if not response.data:
                return {
                    "success": False,
                    "error": f"File at path '{path}' not found in version {version_id}",
                    "error_type": "NOT_FOUND"
                }
                
            return {
                "success": True,
                "data": response.data[0]
            }
        except Exception as e:
            logger.error(f"Error in get_file: {e}")
            return {"success": False, "error": str(e)}
    
    def create_or_update_file(
        self, 
        version_id: Union[str, UUID], 
        path: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        Create or update a file within a version.
        
        Args:
            version_id: UUID of the version
            path: File path
            content: File content
            
        Returns:
            Dictionary with file data or error
        """
        try:
            # Check if file exists
            file_response = self.get_file(version_id, path)
            
            if file_response["success"]:
                # Update existing file
                file_id = file_response["data"]["id"]
                response = self.client.table("files") \
                    .update({"content": content}) \
                    .eq("id", file_id) \
                    .execute()
                
                if not response.data:
                    return {"success": False, "error": "Failed to update file"}
                
                return {"success": True, "data": response.data[0]}
            else:
                # Create new file
                file_data = {
                    "id": str(uuid.uuid4()),
                    "version_id": str(version_id),
                    "path": path,
                    "content": content
                }
                
                response = self.client.table("files").insert(file_data).execute()
                
                if not response.data:
                    return {"success": False, "error": "Failed to create file"}
                
                return {"success": True, "data": response.data[0]}
        except Exception as e:
            logger.error(f"Error in create_or_update_file: {e}")
            return {"success": False, "error": str(e)}
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the Supabase connection.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Simple health check query
            self.client.table("projects").select("id").limit(1).execute()
            
            return {
                "success": True,
                "data": {
                    "status": "healthy",
                    "database": "connected",
                    "connection_type": "supabase"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "data": {
                    "status": "unhealthy",
                    "error": str(e),
                    "connection_type": "supabase"
                }
            }
    
    def create_version(
        self,
        project_id: Union[str, UUID],
        name: str,
        parent_version_number: int,
        project_context: str = "",  # Kept for backward compatibility but not used
        change_request: str = ""    # Kept for backward compatibility but not used
    ) -> Dict[str, Any]:
        """
        Create a new version with basic information.
        Note: This implementation doesn't include AI-generated changes.
        
        Args:
            project_id: UUID of the project
            name: Name for the new version
            parent_version_number: Version number of the parent version
            project_context: Context about the project
            change_request: Description of changes requested
            
        Returns:
            Dictionary with created version data or error
        """
        try:
            # Check if project exists and is active
            project_response = self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            if not project_response["data"]["active"]:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} is inactive",
                    "error_type": "FORBIDDEN"
                }
            
            # Get the parent version
            parent_version_response = self.get_version(project_id, parent_version_number, include_files=True)
            if not parent_version_response["success"]:
                return parent_version_response
            
            parent_version = parent_version_response["data"]
            
            # Get the next version number
            versions_response = self.list_versions(project_id, limit=1)
            if not versions_response["success"]:
                return versions_response
            
            next_version_number = 1
            if versions_response["data"]["items"]:
                next_version_number = max([v["version_number"] for v in versions_response["data"]["items"]]) + 1
            
            # Create the version
            version_data = {
                "id": str(uuid.uuid4()),
                "project_id": str(project_id),
                "version_number": next_version_number,
                "name": name,
                "parent_id": parent_version["id"]
            }
            
            response = self.client.table("versions").insert(version_data).execute()
            
            if not response.data:
                return {"success": False, "error": "Failed to create version"}
            
            new_version = response.data[0]
            
            # Copy files from parent version to new version
            if "files" in parent_version and parent_version["files"]:
                for file in parent_version["files"]:
                    file_data = {
                        "id": str(uuid.uuid4()),
                        "version_id": new_version["id"],
                        "path": file["path"],
                        "content": file["content"]
                    }
                    
                    self.client.table("files").insert(file_data).execute()
            
            # Return the version with files
            return self.get_version(project_id, next_version_number, include_files=True)
            
        except Exception as e:
            logger.error(f"Error in create_version: {e}")
            return {"success": False, "error": str(e)}