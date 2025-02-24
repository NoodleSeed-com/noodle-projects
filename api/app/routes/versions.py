"""Version-specific route handlers."""
from typing import List
from uuid import UUID
import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_db
from ..crud import projects, versions
from ..schemas.version import (
    VersionResponse,
    VersionListItem,
    CreateVersionRequest
)
from ..services.openrouter import get_openrouter

router = APIRouter()

@router.get("/", response_model=List[VersionListItem])
async def list_versions(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List all versions of a project.
    
    Returns a simplified list of versions containing:
    - id: UUID of the version
    - version_number: Sequential version number
    - name: Version name
    
    Versions are ordered by version_number.
    """
    project = await projects.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await versions.get_versions(db, project_id, skip=skip, limit=limit)

@router.get(
    "/{version_number}",
    response_model=VersionResponse
)
async def get_version(
    project_id: UUID,
    version_number: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific version of a project.
    
    Returns full version details including:
    - All standard version fields (id, project_id, version_number, name, etc.)
    - parent_version: The version number of the parent version (if any)
    - parent_id: The UUID of the parent version (maintained for compatibility)
    """
    project = await projects.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    version = await versions.get_version(db, project_id, version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version

@router.post("/", response_model=VersionResponse)
async def create_version(
    project_id: UUID,
    request: CreateVersionRequest,
    db: AsyncSession = Depends(get_db),
    openrouter_service = Depends(get_openrouter)
):
    """Create a new version of a project.
    
    Steps:
    1. Validate project and parent version exist
    2. Check project is active
    3. Get changes from AI
    4. Create new version with changes
    """
    # Check if project exists and is active
    project = await projects.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.active:
        raise HTTPException(
            status_code=403,
            detail="Cannot create version for inactive project"
        )
    
    # Check if parent version exists
    parent_version = await versions.get_version(db, project_id, request.parent_version_number)
    if not parent_version:
        raise HTTPException(status_code=404, detail="Parent version not found")
    
    try:
        # Get changes from OpenRouter service
        changes = await openrouter_service.get_file_changes(
            project_context=request.project_context,
            change_request=request.change_request,
            current_files=parent_version.files
        )
        
        # Create new version with changes
        new_version = await versions.create_version(
            db=db,
            project_id=project_id,
            parent_version_number=request.parent_version_number,
            name=request.name,
            changes=changes
        )
        
        if not new_version:
            raise HTTPException(status_code=500, detail="Failed to create new version")
        
        return new_version
        
    except ValueError as e:
        # Handle validation errors (empty paths, duplicate paths, etc.)
        raise HTTPException(status_code=400, detail=str(e))
    except sqlalchemy.exc.IntegrityError as e:
        # Handle database constraint violations
        raise HTTPException(status_code=409, detail=str(e))
    except sqlalchemy.exc.OperationalError as e:
        # Handle transaction/concurrency errors
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"Error creating version: {str(e)}")
