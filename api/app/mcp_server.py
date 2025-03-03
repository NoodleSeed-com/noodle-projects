from mcp.server.fastmcp import FastMCP
import logging
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

# Import existing business logic
from app.crud.project import ProjectCRUD
from app.crud.version.crud import VersionCRUD
from app.crud.file import FileCRUD
from app.models.project import Project
from app.models.version import Version
from app.models.file import File
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.version import VersionCreate, VersionResponse, VersionWithFilesResponse
from app.schemas.file import FileCreate, FileUpdate, FileChange, FileResponse
from app.schemas.common import PaginationParams
from app.config import get_settings
from app.services.openrouter import OpenRouterService
from app.errors import NoodleError, ErrorType

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db

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
    search: Optional[str] = None
) -> Dict[str, Any]:
    """List all projects with pagination and optional search.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        search: Optional search term for project name or description
        
    Returns:
        List of projects with pagination info
    """
    try:
        crud = ProjectCRUD(session)
        pagination = PaginationParams(skip=skip, limit=limit)
        projects, total = await crud.get_multi(
            pagination=pagination,
            search=search
        )
        
        return {
            "success": True,
            "data": {
                "total": total,
                "items": [p.model_dump() for p in projects],
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
        crud = ProjectCRUD(session)
        project = await crud.get(project_id)
        
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
    description: Optional[str] = None,
    is_active: Optional[bool] = True
) -> Dict[str, Any]:
    """Create a new project.
    
    Args:
        name: Project name
        description: Optional project description
        is_active: Whether the project is active (default: True)
        
    Returns:
        Created project details
    """
    try:
        crud = ProjectCRUD(session)
        project_create = ProjectCreate(
            name=name,
            description=description,
            is_active=is_active
        )
        
        project = await crud.create(project_create)
        
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
    """Delete a project by ID.
    
    Args:
        project_id: UUID of the project to delete
        
    Returns:
        Success status
    """
    try:
        crud = ProjectCRUD(session)
        deleted = await crud.delete(project_id)
        
        if not deleted:
            return {
                "success": False,
                "error": f"Project with ID {project_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        return {
            "success": True,
            "data": {"message": f"Project {project_id} deleted successfully"}
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
        pagination = PaginationParams(skip=skip, limit=limit)
        
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
            pagination=pagination
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
    version_id: UUID,
    include_files: Optional[bool] = False
) -> Dict[str, Any]:
    """Get version details by ID.
    
    Args:
        version_id: UUID of the version
        include_files: Whether to include files in the response
        
    Returns:
        Version details with optional files
    """
    try:
        crud = VersionCRUD(session)
        version = await crud.get(version_id)
        
        if not version:
            return {
                "success": False,
                "error": f"Version with ID {version_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }

        if include_files:
            files = await crud.get_version_files(version_id)
            version_data = VersionWithFilesResponse(
                **version.model_dump(),
                files=[FileResponse.model_validate(file) for file in files]
            )
            return {
                "success": True,
                "data": version_data.model_dump()
            }
        else:
            return {
                "success": True,
                "data": version.model_dump()
            }
    except Exception as e:
        logger.error(f"Error in get_version: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
@with_session
async def create_version(
    session: AsyncSession,
    project_id: UUID,
    parent_version_id: Optional[UUID] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new version for a project.
    
    Args:
        project_id: UUID of the project
        parent_version_id: Optional UUID of the parent version
        description: Optional version description
        
    Returns:
        Created version details
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
            
        # Check parent version if provided
        if parent_version_id:
            parent_version = await crud.get(parent_version_id)
            if not parent_version:
                return {
                    "success": False,
                    "error": f"Parent version with ID {parent_version_id} not found",
                    "error_type": ErrorType.NOT_FOUND.value
                }
                
            # Ensure parent belongs to the same project
            if parent_version.project_id != project_id:
                return {
                    "success": False,
                    "error": "Parent version must belong to the same project",
                    "error_type": ErrorType.VALIDATION_ERROR.value
                }
                
        version_create = VersionCreate(
            project_id=project_id,
            parent_version_id=parent_version_id,
            description=description
        )
        
        version = await crud.create(version_create)
        
        return {
            "success": True,
            "data": version.model_dump()
        }
    except Exception as e:
        logger.error(f"Error in create_version: {e}")
        return {"success": False, "error": str(e)}

# File tools
@mcp.tool()
@with_session
async def get_file(
    session: AsyncSession,
    version_id: UUID,
    file_path: str
) -> Dict[str, Any]:
    """Get file content from a specific version.
    
    Args:
        version_id: UUID of the version
        file_path: Path of the file
        
    Returns:
        File details and content
    """
    try:
        crud = FileCRUD(session)
        
        # Check if version exists
        version_crud = VersionCRUD(session)
        version = await version_crud.get(version_id)
        if not version:
            return {
                "success": False,
                "error": f"Version with ID {version_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        file = await crud.get_by_path(version_id, file_path)
        
        if not file:
            return {
                "success": False,
                "error": f"File with path '{file_path}' not found in version {version_id}",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        return {
            "success": True,
            "data": {
                "id": str(file.id),
                "version_id": str(file.version_id),
                "path": file.path,
                "content": file.content,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "updated_at": file.updated_at.isoformat() if file.updated_at else None
            }
        }
    except Exception as e:
        logger.error(f"Error in get_file: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
@with_session
async def list_files(
    session: AsyncSession,
    version_id: UUID
) -> Dict[str, Any]:
    """List all files in a version.
    
    Args:
        version_id: UUID of the version
        
    Returns:
        List of files in the version
    """
    try:
        crud = VersionCRUD(session)
        
        # Check if version exists
        version = await crud.get(version_id)
        if not version:
            return {
                "success": False,
                "error": f"Version with ID {version_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        files = await crud.get_version_files(version_id)
        
        return {
            "success": True,
            "data": [
                {
                    "id": str(file.id),
                    "version_id": str(file.version_id),
                    "path": file.path,
                    "created_at": file.created_at.isoformat() if file.created_at else None,
                    "updated_at": file.updated_at.isoformat() if file.updated_at else None
                }
                for file in files
            ]
        }
    except Exception as e:
        logger.error(f"Error in list_files: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
@with_session
async def update_file(
    session: AsyncSession,
    version_id: UUID,
    file_path: str,
    content: str
) -> Dict[str, Any]:
    """Update or create a file in a version.
    
    Args:
        version_id: UUID of the version
        file_path: Path of the file
        content: New content for the file
        
    Returns:
        Updated or created file details
    """
    try:
        file_crud = FileCRUD(session)
        version_crud = VersionCRUD(session)
        
        # Check if version exists
        version = await version_crud.get(version_id)
        if not version:
            return {
                "success": False,
                "error": f"Version with ID {version_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        # Check if file exists
        existing_file = await file_crud.get_by_path(version_id, file_path)
        
        if existing_file:
            # Update existing file
            file_update = FileUpdate(content=content)
            updated_file = await file_crud.update(existing_file.id, file_update)
            
            return {
                "success": True,
                "data": {
                    "id": str(updated_file.id),
                    "version_id": str(updated_file.version_id),
                    "path": updated_file.path,
                    "content": updated_file.content,
                    "created_at": updated_file.created_at.isoformat() if updated_file.created_at else None,
                    "updated_at": updated_file.updated_at.isoformat() if updated_file.updated_at else None,
                    "operation": "UPDATE"
                }
            }
        else:
            # Create new file
            file_create = FileCreate(
                version_id=version_id,
                path=file_path,
                content=content
            )
            created_file = await file_crud.create(file_create)
            
            return {
                "success": True,
                "data": {
                    "id": str(created_file.id),
                    "version_id": str(created_file.version_id),
                    "path": created_file.path,
                    "content": created_file.content,
                    "created_at": created_file.created_at.isoformat() if created_file.created_at else None,
                    "updated_at": created_file.updated_at.isoformat() if created_file.updated_at else None,
                    "operation": "CREATE"
                }
            }
    except Exception as e:
        logger.error(f"Error in update_file: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
@with_session
async def delete_file(
    session: AsyncSession,
    version_id: UUID,
    file_path: str
) -> Dict[str, Any]:
    """Delete a file from a version.
    
    Args:
        version_id: UUID of the version
        file_path: Path of the file to delete
        
    Returns:
        Success status
    """
    try:
        file_crud = FileCRUD(session)
        version_crud = VersionCRUD(session)
        
        # Check if version exists
        version = await version_crud.get(version_id)
        if not version:
            return {
                "success": False,
                "error": f"Version with ID {version_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        # Check if file exists
        existing_file = await file_crud.get_by_path(version_id, file_path)
        
        if not existing_file:
            return {
                "success": False,
                "error": f"File with path '{file_path}' not found in version {version_id}",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        # Delete file
        await file_crud.delete(existing_file.id)
        
        return {
            "success": True,
            "data": {
                "message": f"File '{file_path}' deleted successfully from version {version_id}",
                "file_id": str(existing_file.id),
                "version_id": str(version_id),
                "path": file_path
            }
        }
    except Exception as e:
        logger.error(f"Error in delete_file: {e}")
        return {"success": False, "error": str(e)}

# AI integration
@mcp.tool()
@with_session
async def generate_file_changes(
    session: AsyncSession,
    version_id: UUID,
    user_message: str
) -> Dict[str, Any]:
    """Generate file changes using AI based on user message.
    
    Args:
        version_id: UUID of the version
        user_message: User's request for file changes
        
    Returns:
        Generated file changes
    """
    try:
        version_crud = VersionCRUD(session)
        
        # Check if version exists
        version = await version_crud.get(version_id)
        if not version:
            return {
                "success": False,
                "error": f"Version with ID {version_id} not found",
                "error_type": ErrorType.NOT_FOUND.value
            }
            
        # Get version files
        files = await version_crud.get_version_files(version_id)
        
        # Initialize OpenRouter service
        settings = get_settings()
        openrouter_service = OpenRouterService(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model
        )
        
        # Prepare file data for AI
        file_data = {file.path: file.content for file in files}
        
        # Generate changes
        file_changes = await openrouter_service.generate_file_changes(
            file_data=file_data,
            user_message=user_message
        )
        
        return {
            "success": True,
            "data": {
                "version_id": str(version_id),
                "file_changes": [change.model_dump() for change in file_changes]
            }
        }
    except Exception as e:
        logger.error(f"Error in generate_file_changes: {e}")
        return {"success": False, "error": str(e)}

# Main entry point
if __name__ == "__main__":
    mcp.run()