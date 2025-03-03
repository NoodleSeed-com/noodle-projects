"""
MCP server for the Noodle Projects API. This module provides tools for interacting with
the Noodle Projects API using the Model Context Protocol (MCP).
"""
from mcp.server.fastmcp import FastMCP
import logging
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

# Import existing business logic
from app.crud.project import ProjectCRUD
from app.crud.version.crud import VersionCRUD
from app.models.project import Project
from app.models.version import Version
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.version import VersionCreate, VersionResponse, CreateVersionRequest
from app.schemas.common import FileOperation, FileChange
from app.config import settings
from app.services.openrouter import OpenRouterService, get_openrouter
from app.errors import NoodleError, ErrorType

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("NoodleProjects")

# Helper function to get DB session
async def get_session() -> AsyncSession:
    """Get database session."""
    async for session in get_db():
        return session

# Database dependency for MCP tools
def with_session(func):
    """Decorator to provide database session to MCP tools."""
    async def wrapper(*args, **kwargs):
        session = await get_session()
        try:
            return await func(session, *args, **kwargs)
        except NoodleError as e:
            logger.error(f"NoodleError in {func.__name__}: {e}")
            return {"success": False, "error": str(e), "error_type": e.error_type.value}
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return {"success": False, "error": str(e)}
    
    # Preserve function metadata for MCP
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

# Project tools
@mcp.tool()
@with_session
async def list_projects(
    session: AsyncSession,
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
    try:
        projects = await ProjectCRUD.get_multi(
            db=session,
            skip=skip,
            limit=limit
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

@mcp.tool()
@with_session
async def get_project(
    session: AsyncSession,
    project_id: UUID
) -> Dict[str, Any]:
    """Get project details by ID.
    
    Args:
        project_id: UUID of the project
        
    Returns:
        Project details
    """
    try:
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

@mcp.tool()
@with_session
async def create_project(
    session: AsyncSession,
    name: str,
    description: Optional[str] = ""
) -> Dict[str, Any]:
    """Create a new project with an initial version.
    
    Args:
        name: Project name
        description: Optional project description
        
    Returns:
        Created project details
    """
    try:
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

@mcp.tool()
@with_session
async def update_project(
    session: AsyncSession,
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
    try:
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

@mcp.tool()
@with_session
async def delete_project(
    session: AsyncSession,
    project_id: UUID
) -> Dict[str, Any]:
    """Soft-delete a project by setting is_active to false.
    
    Args:
        project_id: UUID of the project to delete
        
    Returns:
        Success status
    """
    try:
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

# Version tools
@mcp.tool()
@with_session
async def list_versions(
    session: AsyncSession,
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
    try:
        crud = VersionCRUD(session)
        
        # Check if project exists
        project_crud = ProjectCRUD(session)
        project = await project_crud.get(project_id)
        if not project:
            return {
                "success": False,
                "error": f"Project with ID {project_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }
        
        versions, total = await crud.get_project_versions(
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

@mcp.tool()
@with_session
async def get_version(
    session: AsyncSession,
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
    try:
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

@mcp.tool()
@with_session
async def create_version(
    session: AsyncSession,
    project_id: UUID,
    name: str,
    parent_version_number: int,
    project_context: str,
    change_request: str
) -> Dict[str, Any]:
    """Create a new version for a project with AI-generated changes.
    
    Args:
        project_id: UUID of the project
        name: Name for the new version
        parent_version_number: Version number of the parent version
        project_context: Context about the project for AI
        change_request: Description of changes requested
        
    Returns:
        Created version details with files
    """
    try:
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
            
        # Prepare the version create request
        version_request = CreateVersionRequest(
            name=name,
            parent_version_number=parent_version_number,
            project_context=project_context,
            change_request=change_request
        )
        
        # Get OpenRouter service
        openrouter_service = await get_openrouter()
        
        # Create the new version
        new_version = await version_crud.create_version_with_changes(
            project_id=project_id,
            parent_version_id=parent_version.id,
            name=version_request.name,
            project_context=version_request.project_context,
            change_request=version_request.change_request,
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

# Main entry point
if __name__ == "__main__":
    mcp.run()