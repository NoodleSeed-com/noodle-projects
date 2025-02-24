"""Core CRUD operations for project versions."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...models.version import Version
from ...models.project import Project
from ...schemas.version import VersionResponse, VersionListItem
from ...schemas.file import FileResponse
from ...schemas.common import FileChange
from .file_operations import validate_file_changes, apply_file_changes

async def get_next_version_number(db: AsyncSession, project_id: UUID) -> int:
    """Get the next available version number for a project.
    
    Args:
        db: Database session
        project_id: Project UUID
        
    Returns:
        Next available version number
    """
    latest_version = await db.execute(
        select(Version.version_number)
        .filter(Version.project_id == project_id)
        .order_by(Version.version_number.desc())
        .with_for_update()  # Lock to prevent concurrent updates
    )
    latest_version = latest_version.scalar_one_or_none()
    return (latest_version or -1) + 1

async def get_version(
    db: AsyncSession,
    project_id: UUID,
    version_number: int
) -> Optional[VersionResponse]:
    """Get a specific version of a project including its files."""
    result = await db.execute(
        select(Version)
        .options(joinedload(Version.files))
        .filter(
            Version.project_id == project_id,
            Version.version_number == version_number
        )
    )
    version = result.unique().scalar_one_or_none()
    
    if not version:
        return None

    # Get parent version number if it exists
    parent_version = None
    if getattr(version, "parent_version_id", None):
        result = await db.execute(
            select(Version.version_number)
            .filter(Version.id == version.parent_version_id)
        )
        parent_version = result.scalar_one_or_none()

    # Convert files to FileResponse objects
    file_responses = [
        FileResponse(
            id=file.id,
            path=file.path,
            content=file.content
        ) for file in version.files
    ]
    
    # Get project's active state
    result = await db.execute(
        select(Project.active)
        .filter(Project.id == version.project_id)
    )
    project_active = result.scalar_one()
    
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        version_number=version.version_number,
        name=version.name,
        parent_version_id=version.parent_version_id,
        parent_version=parent_version,
        created_at=version.created_at,
        updated_at=version.updated_at,
        files=file_responses,
        active=project_active
    )

async def get_versions(
    db: AsyncSession,
    project_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[VersionListItem]:
    """Get all versions of a project.
    
    Only returns versions if the project is active.
    """
    # First check if project is active
    result = await db.execute(
        select(Project.active)
        .filter(Project.id == project_id)
    )
    project_active = result.scalar_one()
    
    # Return empty list if project is inactive
    if not project_active:
        return []
    
    result = await db.execute(
            select(Version.id, Version.version_number, Version.name)
            .filter(Version.project_id == project_id)
            .order_by(Version.version_number)
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()
    return [VersionListItem(id=id, version_number=number, name=name) 
            for id, number, name in rows]

async def create_version(
    db: AsyncSession,
    project_id: UUID,
    parent_version_number: int,
    name: str,
    changes: List[FileChange]
) -> Optional[VersionResponse]:
    """Create a new version based on a parent version and apply changes.
    
    Args:
        db: Database session
        project_id: Project UUID
        parent_version_number: Version number to base the new version on
        name: Name for the new version
        changes: List of file changes to apply
        
    Returns:
        New version with applied changes, or None if parent version not found
        
    Raises:
        ValueError: If file operations are invalid
        sqlalchemy.exc.IntegrityError: If version number conflict occurs
    """
    try:
        async with db.begin():
            # Get parent version with its files and lock the row
            parent_version = await db.execute(
                select(Version)
                .options(joinedload(Version.files))
                .filter(
                    Version.project_id == project_id,
                    Version.version_number == parent_version_number
                )
                .with_for_update()  # Lock the row
            )
            parent_version = parent_version.unique().scalar_one_or_none()
            
            if not parent_version:
                return None

            # Create a map of existing files by path
            existing_files = {file.path: file for file in parent_version.files}
            
            # Validate all file changes before proceeding
            await validate_file_changes(changes, existing_files)
            
            # Get next version number
            new_version_number = await get_next_version_number(db, project_id)
            
            # Create new version
            new_version = Version(
                project_id=project_id,
                version_number=new_version_number,
                parent_version_id=parent_version.id,
                name=name
            )
            db.add(new_version)
            await db.flush()  # Get new_version.id without committing
            
            # Apply file changes
            files_to_add = await apply_file_changes(
                new_version.id,
                changes,
                existing_files
            )
            
            # Set the files relationship
            new_version.files = files_to_add
            db.add(new_version)
            await db.flush()
            await db.refresh(new_version)
            
            # Get version response within same transaction
            return await get_version(db, project_id, new_version.version_number)
            
    except Exception as e:
        # Let the context manager handle rollback
        raise e
