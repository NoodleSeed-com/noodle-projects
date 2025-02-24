"""Project-specific route handlers."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_db
from ..crud import projects, versions
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List all active projects."""
    return await projects.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project."""
    # Create project
    db_project = await projects.create(db, project)
    
    # Create initial version with template files
    await versions.create_initial_version(db, db_project.id)
    
    return db_project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID."""
    project = await projects.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a project."""
    # Get existing project
    existing = await projects.get(db, project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Allow updates if project is active or if we're reactivating
    if not existing.active and (project.active is None or not project.active):
        raise HTTPException(
            status_code=403,
            detail="Cannot modify inactive project. Reactivate the project first."
        )
    
    db_project = await projects.update(db, project_id, project)
    return db_project

@router.delete("/{project_id}", response_model=ProjectResponse)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a project."""
    project = await projects.delete(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
