"""
CRUD operations for files.
"""
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.schemas.file import FileResponse
from app.errors import NoodleError, ErrorType

class FileCRUD:
    """CRUD operations for files."""
    
    @staticmethod
    async def get_by_version(
        db: AsyncSession,
        version_id: UUID
    ) -> List[FileResponse]:
        """Get all files for a specific version.
        
        Args:
            db: Database session
            version_id: UUID of the version
            
        Returns:
            List of file response objects
        """
        result = await db.execute(
            select(File)
            .filter(File.version_id == version_id)
        )
        files = result.scalars().all()
        return [
            FileResponse(
                id=file.id,
                path=file.path,
                content=file.content
            ) for file in files
        ]
    
    @staticmethod
    async def get_by_path(
        db: AsyncSession,
        version_id: UUID,
        path: str
    ) -> Optional[FileResponse]:
        """Get a specific file by its path within a version.
        
        Args:
            db: Database session
            version_id: UUID of the version
            path: File path
            
        Returns:
            File response object or None if not found
        """
        result = await db.execute(
            select(File)
            .filter(
                File.version_id == version_id,
                File.path == path
            )
        )
        file = result.scalar_one_or_none()
        if not file:
            return None
            
        return FileResponse(
            id=file.id,
            path=file.path,
            content=file.content
        )
    
    @staticmethod
    async def create_file(
        db: AsyncSession,
        version_id: UUID,
        path: str,
        content: str
    ) -> FileResponse:
        """Create a new file.
        
        Args:
            db: Database session
            version_id: UUID of the version
            path: File path
            content: File content
            
        Returns:
            Created file response object
        """
        # Check if file already exists
        existing_file = await FileCRUD.get_by_path(db, version_id, path)
        if existing_file:
            raise NoodleError(
                f"File already exists at path '{path}' in version {version_id}",
                ErrorType.CONFLICT
            )
        
        # Create new file
        file = File(
            version_id=version_id,
            path=path,
            content=content
        )
        db.add(file)
        await db.commit()
        await db.refresh(file)
        
        return FileResponse(
            id=file.id,
            path=file.path,
            content=file.content
        )
    
    @staticmethod
    async def update_content(
        db: AsyncSession,
        file_id: UUID,
        content: str
    ) -> FileResponse:
        """Update a file's content.
        
        Args:
            db: Database session
            file_id: UUID of the file
            content: New file content
            
        Returns:
            Updated file response object
        """
        result = await db.execute(
            select(File)
            .filter(File.id == file_id)
        )
        file = result.scalar_one_or_none()
        if not file:
            raise NoodleError(
                f"File with ID {file_id} not found",
                ErrorType.NOT_FOUND
            )
        
        file.content = content
        await db.commit()
        await db.refresh(file)
        
        return FileResponse(
            id=file.id,
            path=file.path,
            content=file.content
        )
    
    @staticmethod
    async def delete_file(
        db: AsyncSession,
        file_id: UUID
    ) -> None:
        """Delete a file.
        
        Args:
            db: Database session
            file_id: UUID of the file
        """
        result = await db.execute(
            select(File)
            .filter(File.id == file_id)
        )
        file = result.scalar_one_or_none()
        if not file:
            raise NoodleError(
                f"File with ID {file_id} not found",
                ErrorType.NOT_FOUND
            )
        
        await db.delete(file)
        await db.commit()
    
    @staticmethod
    async def get_files_dict(
        db: AsyncSession,
        version_id: UUID
    ) -> Dict[str, File]:
        """Get all files for a version as a dictionary keyed by path.
        
        Args:
            db: Database session
            version_id: UUID of the version
            
        Returns:
            Dictionary of files keyed by path
        """
        result = await db.execute(
            select(File)
            .filter(File.version_id == version_id)
        )
        files = result.scalars().all()
        return {file.path: file for file in files}