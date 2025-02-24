"""Template handling for initial version creation."""
import os
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
    for root, _, files in os.walk(template_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, template_dir)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            db_file = File(
                version_id=db_version.id,
                path=relative_path,
                content=content
            )
            db.add(db_file)
    
    await db.commit()
    return db_version
