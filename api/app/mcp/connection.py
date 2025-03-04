"""
Database connection abstraction for MCP server.
Supports both direct SQLAlchemy connections and Supabase REST API.
"""
import os
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_db
from app.crud.project import ProjectCRUD
from app.crud.version.crud import VersionCRUD
from app.models.project import Project, ProjectCreate, ProjectUpdate
from app.models.version import Version, VersionCreate, VersionResponse
from app.errors import NoodleError, ErrorType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://jsanjojgtyyfpnfqwhgx.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM")

class DatabaseConnection:
    """Abstract base class for database connections."""
    
    async def list_projects(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> Dict[str, Any]:
        """List all projects with pagination."""
        raise NotImplementedError
    
    async def get_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get a project by ID."""
        raise NotImplementedError
    
    async def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new project."""
        raise NotImplementedError
    
    async def update_project(self, project_id: Union[str, UUID], name: Optional[str] = None, 
                           description: Optional[str] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Update a project."""
        raise NotImplementedError
    
    async def delete_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """Soft-delete a project."""
        raise NotImplementedError
    
    async def list_versions(self, project_id: Union[str, UUID], skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List all versions for a project."""
        raise NotImplementedError
    
    async def get_version(self, project_id: Union[str, UUID], version_number: int, include_files: bool = True) -> Dict[str, Any]:
        """Get a version by project ID and version number."""
        raise NotImplementedError
    
    async def create_version(self, project_id: Union[str, UUID], name: str, 
                            parent_version_number: int, project_context: str, 
                            change_request: str) -> Dict[str, Any]:
        """Create a new version with AI-generated changes."""
        raise NotImplementedError
    
    async def get_file(self, version_id: Union[str, UUID], path: str) -> Dict[str, Any]:
        """Get a file by version ID and path."""
        raise NotImplementedError
    
    async def create_or_update_file(self, version_id: Union[str, UUID], path: str, content: str) -> Dict[str, Any]:
        """Create or update a file within a version."""
        raise NotImplementedError
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the database connection."""
        raise NotImplementedError

class SQLAlchemyConnection(DatabaseConnection):
    """Direct SQLAlchemy database connection."""
    
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        async for session in get_db():
            return session
    
    async def list_projects(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> Dict[str, Any]:
        """List all projects with pagination."""
        try:
            session = await self.get_session()
            projects = await ProjectCRUD.get_multi(
                db=session,
                skip=skip,
                limit=limit,
                include_inactive=include_inactive
            )
            total = len(projects)
            
            return {
                "success": True,
                "data": {
                    "total": total,
                    "items": [project.model_dump() for project in projects],
                    "skip": skip,
                    "limit": limit
                }
            }
        except Exception as e:
            logger.error(f"Error in list_projects: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get a project by ID."""
        try:
            session = await self.get_session()
            project = await ProjectCRUD.get(db=session, project_id=project_id)
            
            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            return {
                "success": True,
                "data": project.model_dump()
            }
        except Exception as e:
            logger.error(f"Error in get_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new project."""
        try:
            session = await self.get_session()
            project_create = ProjectCreate(
                name=name,
                description=description
            )
            
            project = await ProjectCRUD.create(db=session, project=project_create)
            
            return {
                "success": True,
                "data": project.model_dump()
            }
        except Exception as e:
            logger.error(f"Error in create_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_project(self, project_id: Union[str, UUID], name: Optional[str] = None, 
                           description: Optional[str] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Update a project."""
        try:
            session = await self.get_session()
            crud = ProjectCRUD(session)
            
            # Only include non-None fields
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if is_active is not None:
                update_data["is_active"] = is_active
                
            project_update = ProjectUpdate(**update_data)
            
            project = await crud.update(project_id, project_update)
            
            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            return {
                "success": True,
                "data": project.model_dump()
            }
        except Exception as e:
            logger.error(f"Error in update_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """Soft-delete a project."""
        try:
            session = await self.get_session()
            crud = ProjectCRUD(session)
            project_update = ProjectUpdate(is_active=False)
            project = await crud.update(project_id, project_update)
            
            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            return {
                "success": True,
                "data": project.model_dump()
            }
        except Exception as e:
            logger.error(f"Error in delete_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_versions(self, project_id: Union[str, UUID], skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List all versions for a project."""
        try:
            session = await self.get_session()
            
            # Check if project exists
            project_crud = ProjectCRUD(session)
            project = await project_crud.get(project_id)
            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
            
            version_crud = VersionCRUD(session)
            versions, total = await version_crud.get_project_versions(
                project_id=project_id,
                pagination={"skip": skip, "limit": limit}
            )
            
            return {
                "success": True,
                "data": {
                    "total": total,
                    "items": [v.model_dump() for v in versions],
                    "skip": skip,
                    "limit": limit
                }
            }
        except Exception as e:
            logger.error(f"Error in list_versions: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_version(self, project_id: Union[str, UUID], version_number: int, include_files: bool = True) -> Dict[str, Any]:
        """Get a version by project ID and version number."""
        try:
            session = await self.get_session()
            
            # Check if project exists
            project_crud = ProjectCRUD(session)
            project = await project_crud.get(project_id)
            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            # Get the version
            version_crud = VersionCRUD(session)
            version = await version_crud.get_by_number(project_id, version_number)
            
            if not version:
                return {
                    "success": False,
                    "error": f"Version {version_number} not found for project {project_id}",
                    "error_type": ErrorType.NOT_FOUND.value
                }

            response_data = version

            # Include files if requested
            if include_files:
                files = await version_crud.get_version_files(version.id)
                response_data = version_crud.serialize_version_with_files(version, files)
                
            return {
                "success": True,
                "data": response_data
            }
        except Exception as e:
            logger.error(f"Error in get_version: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_version(self, project_id: Union[str, UUID], name: str, 
                           parent_version_number: int, project_context: str, 
                           change_request: str) -> Dict[str, Any]:
        """Create a new version with AI-generated changes."""
        try:
            session = await self.get_session()
            
            # Check if project exists and is active
            project_crud = ProjectCRUD(session)
            project = await project_crud.get(project_id)
            
            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            if not project.is_active:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} is inactive",
                    "error_type": ErrorType.FORBIDDEN.value
                }
                
            # Get the parent version
            version_crud = VersionCRUD(session)
            parent_version = await version_crud.get_by_number(project_id, parent_version_number)
            
            if not parent_version:
                return {
                    "success": False,
                    "error": f"Parent version {parent_version_number} not found for project {project_id}",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            # Get OpenRouter service
            from app.services.openrouter import get_openrouter
            openrouter_service = await get_openrouter()
            
            # Create the new version
            new_version = await version_crud.create_version_with_changes(
                project_id=project_id,
                parent_version_id=parent_version.id,
                name=name,
                project_context=project_context,
                change_request=change_request,
                ai_service=openrouter_service
            )
            
            # Get the files for the new version
            files = await version_crud.get_version_files(new_version.id)
            
            # Return the version with files
            response_data = version_crud.serialize_version_with_files(new_version, files)
            
            return {
                "success": True,
                "data": response_data
            }
        except Exception as e:
            logger.error(f"Error in create_version: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_file(self, version_id: Union[str, UUID], path: str) -> Dict[str, Any]:
        """Get a file by version ID and path."""
        try:
            session = await self.get_session()
            from app.crud.file import FileCRUD
            
            file = await FileCRUD.get_by_path(db=session, version_id=version_id, path=path)
            
            if not file:
                return {
                    "success": False,
                    "error": f"File not found at path '{path}' in version {version_id}",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            return {
                "success": True,
                "data": file.model_dump()
            }
        except Exception as e:
            logger.error(f"Error in get_file: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_or_update_file(self, version_id: Union[str, UUID], path: str, content: str) -> Dict[str, Any]:
        """Create or update a file within a version."""
        try:
            session = await self.get_session()
            from app.crud.file import FileCRUD
            
            # Check if version exists
            from app.crud.version.crud import VersionCRUD
            version_crud = VersionCRUD(session)
            version = await version_crud.get(version_id)
            
            if not version:
                return {
                    "success": False,
                    "error": f"Version with ID {version_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            # Check if file exists
            file = await FileCRUD.get_by_path(db=session, version_id=version_id, path=path)
            
            if file:
                # Update existing file
                updated_file = await FileCRUD.update_content(
                    db=session,
                    file_id=file.id,
                    content=content
                )
                
                return {
                    "success": True,
                    "data": updated_file.model_dump()
                }
            else:
                # Create new file
                new_file = await FileCRUD.create_file(
                    db=session,
                    version_id=version_id,
                    path=path,
                    content=content
                )
                
                return {
                    "success": True,
                    "data": new_file.model_dump()
                }
        except Exception as e:
            logger.error(f"Error in create_or_update_file: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the SQLAlchemy connection."""
        try:
            session = await self.get_session()
            
            # Try a simple query to check connectivity
            await ProjectCRUD.get_multi(db=session, limit=1)
            
            # Check OpenRouter connectivity
            openrouter_status = "unknown"
            try:
                from app.services.openrouter import get_openrouter
                openrouter = await get_openrouter()
                if openrouter:
                    openrouter_status = "connected"
            except Exception:
                openrouter_status = "error"
            
            return {
                "success": True,
                "data": {
                    "status": "healthy",
                    "database": "connected",
                    "openrouter": openrouter_status,
                    "connection_type": "sqlalchemy"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "data": {
                    "status": "unhealthy",
                    "error": str(e),
                    "connection_type": "sqlalchemy"
                }
            }


class SupabaseRESTConnection(DatabaseConnection):
    """Supabase REST API connection."""
    
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
    
    async def list_projects(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> Dict[str, Any]:
        """List all projects with pagination."""
        try:
            # Build query filters
            active_filter = "" if include_inactive else "&is_active=eq.true"
            
            response = requests.get(
                f"{self.url}/rest/v1/projects?select=*&order=created_at.desc&limit={limit}&offset={skip}{active_filter}",
                headers=self.headers
            )
            response.raise_for_status()
            projects = response.json()
            
            return {
                "success": True,
                "data": {
                    "total": len(projects),  # Simplified count
                    "items": projects,
                    "skip": skip,
                    "limit": limit
                }
            }
        except Exception as e:
            logger.error(f"Error in list_projects: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get a project by ID."""
        try:
            response = requests.get(
                f"{self.url}/rest/v1/projects?id=eq.{project_id}&select=*",
                headers=self.headers
            )
            response.raise_for_status()
            projects = response.json()
            
            if not projects:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            return {
                "success": True,
                "data": projects[0]
            }
        except Exception as e:
            logger.error(f"Error in get_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new project."""
        try:
            project_data = {
                "name": name,
                "description": description,
                "is_active": True
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
                return {"success": True, "data": created_project[0]}
            elif isinstance(created_project, dict):
                return {"success": True, "data": created_project}
            else:
                # If we can't get data from response, query for the project we just created
                get_response = requests.get(
                    f"{self.url}/rest/v1/projects?name=eq.{name}&order=created_at.desc&limit=1",
                    headers=self.headers
                )
                get_response.raise_for_status()
                projects = get_response.json()
                if projects and len(projects) > 0:
                    return {"success": True, "data": projects[0]}
                raise ValueError("Could not retrieve created project")
        except Exception as e:
            logger.error(f"Error in create_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_project(self, project_id: Union[str, UUID], name: Optional[str] = None, 
                           description: Optional[str] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Update a project."""
        try:
            # Check if project exists
            project_response = await self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if is_active is not None:
                update_data["is_active"] = is_active
            
            if not update_data:
                # Nothing to update, return current project
                return project_response
                
            # For PATCH operations, we need to add updated_at
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Add a special header to get the updated data back directly
            patch_headers = self.headers.copy()
            patch_headers["Prefer"] = "return=representation"
                
            response = requests.patch(
                f"{self.url}/rest/v1/projects?id=eq.{project_id}",
                headers=patch_headers,
                json=update_data
            )
            
            # If we got back data, return that directly
            if response.status_code == 200 and response.content:
                try:
                    updated_data = response.json()
                    if isinstance(updated_data, list) and len(updated_data) > 0:
                        return {"success": True, "data": updated_data[0]}
                except:
                    pass
            
            # If the PATCH didn't return data or failed, get the project
            if response.status_code not in [200, 204]:
                raise ValueError(f"Failed to update project: {response.text}")
                
            # Get the updated project
            return await self.get_project(project_id)
        except Exception as e:
            logger.error(f"Error in update_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_project(self, project_id: Union[str, UUID]) -> Dict[str, Any]:
        """Soft-delete a project."""
        try:
            # Check if project exists
            project_response = await self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            # We use soft delete by setting is_active=false
            update_data = {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = requests.patch(
                f"{self.url}/rest/v1/projects?id=eq.{project_id}",
                headers=self.headers,
                json=update_data
            )
            
            # Check for success (either 200 or 204)
            if response.status_code in [200, 204]:
                return {"success": True, "data": project_response["data"]}
            else:
                return {"success": False, "error": f"Failed to delete project: {response.text}"}
        except Exception as e:
            logger.error(f"Error in delete_project: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_versions(self, project_id: Union[str, UUID], skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List all versions for a project."""
        try:
            # Check if project exists
            project_response = await self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            response = requests.get(
                f"{self.url}/rest/v1/versions?project_id=eq.{project_id}&select=*&order=version_number.desc&limit={limit}&offset={skip}",
                headers=self.headers
            )
            response.raise_for_status()
            versions = response.json()
            
            return {
                "success": True,
                "data": {
                    "total": len(versions),  # Simplified count
                    "items": versions,
                    "skip": skip,
                    "limit": limit
                }
            }
        except Exception as e:
            logger.error(f"Error in list_versions: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_version(self, project_id: Union[str, UUID], version_number: int, include_files: bool = True) -> Dict[str, Any]:
        """Get a version by project ID and version number."""
        try:
            # Check if project exists
            project_response = await self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            # Get the version
            response = requests.get(
                f"{self.url}/rest/v1/versions?project_id=eq.{project_id}&version_number=eq.{version_number}&select=*",
                headers=self.headers
            )
            response.raise_for_status()
            versions = response.json()
            
            if not versions:
                return {
                    "success": False,
                    "error": f"Version {version_number} not found for project {project_id}",
                    "error_type": ErrorType.NOT_FOUND.value
                }
            
            version = versions[0]
            
            # Include files if requested
            if include_files:
                files_response = requests.get(
                    f"{self.url}/rest/v1/files?version_id=eq.{version['id']}&select=*",
                    headers=self.headers
                )
                files_response.raise_for_status()
                files = files_response.json()
                
                # Add files to version data
                version["files"] = files
            
            return {
                "success": True,
                "data": version
            }
        except Exception as e:
            logger.error(f"Error in get_version: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_version(self, project_id: Union[str, UUID], name: str, 
                           parent_version_number: int, project_context: str, 
                           change_request: str) -> Dict[str, Any]:
        """Create a new version with AI-generated changes."""
        try:
            # This implementation is simplified since OpenRouter integration 
            # would be complex to replicate with the REST API
            
            # Check if project exists and is active
            project_response = await self.get_project(project_id)
            if not project_response["success"]:
                return project_response
            
            # Check if project is active
            if not project_response["data"]["is_active"]:
                return {
                    "success": False,
                    "error": f"Project with ID {project_id} is inactive",
                    "error_type": ErrorType.FORBIDDEN.value
                }
            
            # Get the parent version
            parent_version_response = await self.get_version(project_id, parent_version_number, include_files=True)
            if not parent_version_response["success"]:
                return parent_version_response
            
            parent_version = parent_version_response["data"]
            
            # Get the next version number
            versions_response = await self.list_versions(project_id, limit=1)
            if not versions_response["success"]:
                return versions_response
            
            next_version_number = 1
            if versions_response["data"]["items"]:
                next_version_number = max([v["version_number"] for v in versions_response["data"]["items"]]) + 1
            
            # Create the version
            version_data = {
                "project_id": str(project_id),
                "version_number": next_version_number,
                "name": name,
                "parent_id": parent_version["id"],
                "project_context": project_context,
                "change_request": change_request
            }
            
            response = requests.post(
                f"{self.url}/rest/v1/versions",
                headers=self.headers,
                json=version_data
            )
            response.raise_for_status()
            created_version = response.json()
            
            if isinstance(created_version, list) and len(created_version) > 0:
                new_version = created_version[0]
            elif isinstance(created_version, dict):
                new_version = created_version
            else:
                # If we can't get data from response, query for the version we just created
                get_response = requests.get(
                    f"{self.url}/rest/v1/versions?project_id=eq.{project_id}&version_number=eq.{next_version_number}",
                    headers=self.headers
                )
                get_response.raise_for_status()
                versions = get_response.json()
                if not versions:
                    raise ValueError("Could not retrieve created version")
                new_version = versions[0]
            
            # Copy files from parent version to new version
            if "files" in parent_version and parent_version["files"]:
                for file in parent_version["files"]:
                    file_data = {
                        "version_id": new_version["id"],
                        "path": file["path"],
                        "content": file["content"]
                    }
                    
                    # Create file in new version
                    file_response = requests.post(
                        f"{self.url}/rest/v1/files",
                        headers=self.headers,
                        json=file_data
                    )
                    file_response.raise_for_status()
            
            # Return the version with files
            return await self.get_version(project_id, next_version_number, include_files=True)
            
        except Exception as e:
            logger.error(f"Error in create_version: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_file(self, version_id: Union[str, UUID], path: str) -> Dict[str, Any]:
        """Get a file by version ID and path."""
        try:
            # URL encode the path to handle special characters
            encoded_path = requests.utils.quote(path)
            response = requests.get(
                f"{self.url}/rest/v1/files?version_id=eq.{version_id}&path=eq.{encoded_path}&select=*",
                headers=self.headers
            )
            response.raise_for_status()
            files = response.json()
            
            if not files:
                return {
                    "success": False,
                    "error": f"File at path '{path}' not found in version {version_id}",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            return {
                "success": True,
                "data": files[0]
            }
        except Exception as e:
            logger.error(f"Error in get_file: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_or_update_file(self, version_id: Union[str, UUID], path: str, content: str) -> Dict[str, Any]:
        """Create or update a file within a version."""
        try:
            # First check if file exists
            file_response = await self.get_file(version_id, path)
            
            if file_response["success"]:
                # Update existing file
                existing_file = file_response["data"]
                response = requests.patch(
                    f"{self.url}/rest/v1/files?id=eq.{existing_file['id']}",
                    headers=self.headers,
                    json={"content": content, "updated_at": datetime.now(timezone.utc).isoformat()}
                )
                response.raise_for_status()
                
                # Get updated file
                return await self.get_file(version_id, path)
            else:
                # Create new file
                file_data = {
                    "version_id": str(version_id),
                    "path": path,
                    "content": content
                }
                
                response = requests.post(
                    f"{self.url}/rest/v1/files",
                    headers=self.headers,
                    json=file_data
                )
                response.raise_for_status()
                
                # Get created file
                return await self.get_file(version_id, path)
        except Exception as e:
            logger.error(f"Error in create_or_update_file: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the Supabase REST API connection."""
        try:
            # Check database connectivity with a simple query
            response = requests.get(
                f"{self.url}/rest/v1/projects?limit=1",
                headers=self.headers
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "data": {
                    "status": "healthy",
                    "database": "connected",
                    "connection_type": "supabase_rest"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "data": {
                    "status": "unhealthy",
                    "error": str(e),
                    "connection_type": "supabase_rest"
                }
            }

def get_connection(connection_type: str = None) -> DatabaseConnection:
    """Get the appropriate database connection based on configuration.
    
    Args:
        connection_type: Optional connection type ('sqlalchemy' or 'supabase_rest').
            If not provided, uses the environment variable NOODLE_DB_CONNECTION_TYPE
            or defaults to 'sqlalchemy'.
            
    Returns:
        DatabaseConnection: The configured database connection.
    """
    if connection_type is None:
        # Use environment variable or default
        connection_type = os.environ.get("NOODLE_DB_CONNECTION_TYPE", "sqlalchemy")
    
    connection_type = connection_type.lower()
    
    if connection_type == "supabase_rest":
        return SupabaseRESTConnection()
    else:
        return SQLAlchemyConnection()