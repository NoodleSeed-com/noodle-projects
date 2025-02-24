"""CRUD operations for files."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.file import File
from ..schemas.file import FileResponse

class FileCRUD:
    """CRUD operations for files"""
    
    @staticmethod
    async def get_by_version(
        db: AsyncSession,
        version_id: UUID
    ) -> List[FileResponse]:
        """Get all files for a specific version."""
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
        """Get a specific file by its path within a version."""
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
