"""Project-specific route handlers using Supabase."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Query

from ..crud.project import ProjectCRUD
from ..crud.version import VersionCRUD
from ..models.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ..errors import NoodleError, ErrorType

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all active projects."""
    return ProjectCRUD.get_multi(skip=skip, limit=limit)

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project: ProjectCreate
):
    """Create a new project."""
    # Create project
    db_project = ProjectCRUD.create(project)
    
    # Create initial version with template files
    VersionCRUD.create_initial_version(db_project.id)
    
    return db_project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID
):
    """Get a specific project by ID."""
    project = ProjectCRUD.get(project_id)
    if not project:
        raise NoodleError("Project not found", ErrorType.NOT_FOUND)
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project: ProjectUpdate
):
    """Update a project."""
    # Get existing project
    existing = ProjectCRUD.get(project_id)
    if not existing:
        raise NoodleError("Project not found", ErrorType.NOT_FOUND)
    
    # Allow updates if project is active or if we're reactivating
    if not existing.is_active and (project.active is None or not project.active):
        raise NoodleError(
            "Cannot modify inactive project. Reactivate the project first.",
            ErrorType.PERMISSION
        )
    
    db_project = ProjectCRUD.update(project_id, project)
    return db_project

@router.delete("/{project_id}", response_model=ProjectResponse)
def delete_project(
    project_id: UUID
):
    """Soft delete a project by setting is_active=False.
    
    This prevents further modifications to the project while still allowing read access.
    All versions associated with the project will also be considered inactive.
    """
    # Check if project exists
    project = ProjectCRUD.get(project_id)
    if not project:
        raise NoodleError("Project not found", ErrorType.NOT_FOUND)
    
    # Check if already inactive
    if not project.is_active:
        # Already inactive, just return it
        return project
    
    # Perform the soft delete
    return ProjectCRUD.delete(project_id)
