"""Template handling for initial version creation."""
import os
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.version import Version
from ...models.file import File

async def create_initial_version(db: AsyncSession, project_id: UUID) -> Version:
    """Create version 0 with template files for a new project."""
    db_version = Version(
        project_id=project_id,
        version_number=0,
        name="Initial Version"
    )
    db.add(db_version)
    await db.commit()
    await db.refresh(db_version)

    # Read and add template files
    template_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates', 'version-0')
    
    # Use asyncio.to_thread for file operations to avoid blocking the event loop
    async def read_file_async(file_path):
        def read_file():
            with open(file_path, 'r') as f:
                return f.read()
        return await asyncio.to_thread(read_file)
    
    # Collect all files first
    file_paths = []
    for root, _, files in os.walk(template_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, template_dir)
            file_paths.append((file_path, relative_path))
    
    # Process files in parallel
    for file_path, relative_path in file_paths:
        content = await read_file_async(file_path)
        
        db_file = File(
            version_id=db_version.id,
            path=relative_path,
            content=content
        )
        db.add(db_file)
    
    await db.commit()
    return db_version
