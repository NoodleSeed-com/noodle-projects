"""Version-specific route handlers."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path

from ..services.openrouter import get_openrouter
from ..models.version import (
    VersionResponse,
    VersionListItem,
    CreateVersionRequest
)
from ..services.openrouter import get_openrouter
from ..errors import NoodleError, ErrorType

router = APIRouter()

@router.get("/", response_model=List[VersionListItem])
def list_versions(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all versions of a project.
    
    Returns a simplified list of versions containing:
    - id: UUID of the version
    - version_number: Sequential version number
    - name: Version name
    
    Versions are ordered by version_number.
    """
    from ..crud.project import ProjectCRUD
    from ..crud.version.crud import VersionCRUD
    
    project = ProjectCRUD.get(project_id)
    if not project:
        raise NoodleError("Project not found", ErrorType.NOT_FOUND)
    return VersionCRUD.get_versions(project_id, skip=skip, limit=limit)

@router.get(
    "/{version_number}",
    response_model=VersionResponse
)
def get_version(
    project_id: UUID,
    version_number: int = Path(..., ge=0)
):
    """Get a specific version of a project.
    
    Returns full version details including:
    - All standard version fields (id, project_id, version_number, name, etc.)
    - parent_version: The version number of the parent version (if any)
    - parent_id: The UUID of the parent version (maintained for compatibility)
    """
    from ..crud.project import ProjectCRUD
    from ..crud.version.crud import VersionCRUD
    
    project = ProjectCRUD.get(project_id)
    if not project:
        raise NoodleError("Project not found", ErrorType.NOT_FOUND)
    
    version = VersionCRUD.get_version(project_id, version_number)
    if not version:
        raise NoodleError("Version not found", ErrorType.NOT_FOUND)
    return version

@router.post("/", response_model=VersionResponse)
def create_version(
    project_id: UUID,
    request: CreateVersionRequest,
    openrouter_service = Depends(get_openrouter)
):
    """Create a new version of a project.
    
    Steps:
    1. Validate project and parent version exist
    2. Check project is active
    3. Get changes from AI
    4. Create new version with changes
    """
    from ..crud.project import ProjectCRUD
    from ..crud.version.crud import VersionCRUD
    
    # Check if project exists and is active
    project = ProjectCRUD.get(project_id)
    if not project:
        raise NoodleError("Project not found", ErrorType.NOT_FOUND)
    if not project.is_active:
        raise NoodleError(
            "Cannot create version for inactive project",
            ErrorType.PERMISSION
        )
    
    # Check if parent version exists
    parent_version = VersionCRUD.get_version(project_id, request.parent_version_number)
    if not parent_version:
        raise NoodleError("Parent version not found", ErrorType.NOT_FOUND)
    
    try:
        # Get changes from OpenRouter service
        try:
            changes = openrouter_service.get_file_changes(
                project_context=request.project_context,
                change_request=request.change_request,
                current_files=parent_version.files
            )
            print(f"DEBUG: Got changes from OpenRouter: {changes}")
        except Exception as e:
            print(f"ERROR: OpenRouter service failed: {e}")
            raise NoodleError(f"Service error: {str(e)}", ErrorType.SERVICE_ERROR)
        
        # Create new version with changes
        new_version = VersionCRUD.create_version(
            project_id=project_id,
            parent_version_number=request.parent_version_number,
            name=request.name,
            changes=changes
        )
        
        if not new_version:
            raise NoodleError("Failed to create new version", ErrorType.DATABASE)
        
        return new_version
        
    except ValueError as e:
        # Handle validation errors (empty paths, duplicate paths, etc.)
        raise NoodleError(str(e), ErrorType.VALIDATION)
    except Exception as e:
        # Handle unexpected errors
        if "is not a valid FileOperation" in str(e):
            raise NoodleError(f"Invalid file operation: {str(e)}", ErrorType.VALIDATION)
        raise NoodleError(f"Error creating version: {str(e)}", ErrorType.DATABASE)
