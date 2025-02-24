"""
Projects API endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
import sqlalchemy.exc

from .config import settings, get_db
from .crud import projects as crud
from typing import Annotated
from .models.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectVersionResponse,
    ProjectVersionListItem,
    CreateVersionRequest
)

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all active projects."""
    return crud.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project."""
    return crud.create(db, project)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific project by ID."""
    project = crud.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project."""
    # Get existing project
    existing = crud.get(db, project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Allow updates if project is active or if we're reactivating
    if not existing.active and (project.active is None or not project.active):
        raise HTTPException(
            status_code=403,
            detail="Cannot modify inactive project. Reactivate the project first."
        )
    
    db_project = crud.update(db, project_id, project)
    return db_project

@router.delete("/{project_id}", response_model=ProjectResponse)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Soft delete a project."""
    project = crud.delete(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("/{project_id}/versions", response_model=List[ProjectVersionListItem])
def list_project_versions(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all versions of a project.
    
    Returns a simplified list of versions containing:
    - id: UUID of the version
    - version_number: Sequential version number
    - name: Version name
    
    Versions are ordered by version_number.
    """
    project = crud.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_versions(db, project_id, skip=skip, limit=limit)

@router.get(
    "/{project_id}/versions/{version_number}",
    response_model=ProjectVersionResponse
)
def get_project_version(
    project_id: UUID,
    version_number: int = Path(..., ge=0),
    db: Session = Depends(get_db)
):
    """Get a specific version of a project.
    
    Returns full version details including:
    - All standard version fields (id, project_id, version_number, name, etc.)
    - parent_version: The version number of the parent version (if any)
    - parent_version_id: The UUID of the parent version (maintained for compatibility)
    """
    project = crud.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    version = crud.get_version(db, project_id, version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version

from app.services.openrouter import get_openrouter

@router.post("/{project_id}/versions", response_model=ProjectVersionResponse)
def create_project_version(
    project_id: UUID,
    request: CreateVersionRequest,
    db: Session = Depends(get_db),
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
    project = crud.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.active:
        raise HTTPException(
            status_code=403,
            detail="Cannot create version for inactive project"
        )
    
    # Check if parent version exists
    parent_version = crud.get_version(db, project_id, request.parent_version_number)
    if not parent_version:
        raise HTTPException(status_code=404, detail="Parent version not found")
    
    try:
        # Get changes from OpenRouter service
        changes = openrouter_service.get_file_changes(
            project_context=request.project_context,
            change_request=request.change_request,
            current_files=parent_version.files
        )
        
        # Create new version with changes
        new_version = crud.create_version(
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
