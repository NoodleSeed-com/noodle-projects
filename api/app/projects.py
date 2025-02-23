"""
Projects API endpoints.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from .config import settings, get_db
from .crud import projects as crud
from .models.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectVersionResponse
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
    db_project = crud.update(db, project_id, project)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
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

@router.get("/{project_id}/versions", response_model=List[ProjectVersionResponse])
def list_project_versions(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all versions of a project."""
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
    """Get a specific version of a project."""
    project = crud.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    version = crud.get_version(db, project_id, version_number)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version
