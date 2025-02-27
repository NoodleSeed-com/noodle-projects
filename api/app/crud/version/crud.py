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
from .template import create_initial_version

class VersionCRUD:
    """CRUD operations for versions"""
    
    @staticmethod
    async def create_initial_version(db: AsyncSession, project_id: UUID) -> Version:
        """Create version 0 with template files for a new project.
        
        Args:
            db: Database session
            project_id: Project UUID
            
        Returns:
            Created initial version
        """
        return await create_initial_version(db, project_id)
    
    @staticmethod
    async def get_version(db: AsyncSession, project_id: UUID, version_number: int) -> Optional[VersionResponse]:
        """Get a specific version of a project.
        
        This is an alias for the get() method to maintain consistency with route naming.
        
        Args:
            db: Database session
            project_id: Project UUID
            version_number: Version number
            
        Returns:
            Version response or None if not found
        """
        return await VersionCRUD.get(db, project_id, version_number)
    
    @staticmethod
    async def get_versions(db: AsyncSession, project_id: UUID, skip: int = 0, limit: int = 100) -> List[VersionListItem]:
        """Get all versions of a project.
        
        This is an alias for the get_multi() method to maintain consistency with route naming.
        
        Args:
            db: Database session
            project_id: Project UUID
            skip: Number of versions to skip
            limit: Maximum number of versions to return
            
        Returns:
            List of version list items
        """
        return await VersionCRUD.get_multi(db, project_id, skip, limit)
    
    @staticmethod
    async def get_next_number(db: AsyncSession, project_id: UUID) -> int:
        """Get the next available version number for a project.
        
        Args:
            db: Database session
            project_id: Project UUID
            
        Returns:
            Next available version number (always >= 1, since 0 is reserved for initial version)
        """
        latest_version = await db.execute(
            select(Version.version_number)
            .filter(Version.project_id == project_id)
            .order_by(Version.version_number.desc())
            # Execute with populate_existing option to avoid locking issues in tests
            .execution_options(populate_existing=True)
        )
        latest_version = latest_version.scalar_one_or_none()
        next_number = (latest_version or 0) + 1
        # Ensure we never return 0, as it's reserved for the initial version
        # IMPORTANT: This needs to be 1 for the test to pass, since 0 is reserved
        return max(1, next_number)

    @staticmethod
    async def get(
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
        if getattr(version, "parent_id", None):
            result = await db.execute(
                select(Version.version_number)
                .filter(Version.id == version.parent_id)
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
            parent_id=version.parent_id,
            parent_version=parent_version,
            created_at=version.created_at,
            updated_at=version.updated_at,
            files=file_responses,
            active=project_active
        )

    @staticmethod
    async def get_multi(
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

    @staticmethod
    async def create_version(
        db: AsyncSession,
        project_id: UUID,
        parent_version_number: int,
        name: str,
        changes: List[FileChange]
    ) -> Optional[VersionResponse]:
        """Create a new version based on a parent version and apply changes.
        
        This is an alias for the create() method to maintain consistency with route naming.
        
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
        return await VersionCRUD.create(db, project_id, parent_version_number, name, changes)
        
    @staticmethod
    async def create(
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
        # No need to manually handle transactions as they should be managed by the caller
        # This function now assumes it's being called within a transaction
        
        # Get parent version with its files
        parent_version = await db.execute(
            select(Version)
            .options(joinedload(Version.files))
            .filter(
                Version.project_id == project_id,
                Version.version_number == parent_version_number
            )
            .execution_options(populate_existing=True)
        )
        parent_version = parent_version.unique().scalar_one_or_none()
        
        if not parent_version:
            return None

        # Create a map of existing files by path
        existing_files = {file.path: file for file in parent_version.files}
        
        # Validate all file changes before proceeding
        # This may raise ValueError which will be caught by the caller
        await validate_file_changes(changes, existing_files)
        
        # Get next version number
        new_version_number = await VersionCRUD.get_next_number(db, project_id)
        
        # Create new version
        new_version = Version(
            project_id=project_id,
            version_number=new_version_number,
            parent_id=parent_version.id,
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
        
        # Return the version response
        return await VersionCRUD.get(db, project_id, new_version.version_number)
