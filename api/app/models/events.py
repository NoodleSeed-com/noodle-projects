"""
SQLAlchemy event listeners for model validation and lifecycle hooks.
"""
import os
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from .project import Project
from .version import Version
from .file import File

@event.listens_for(Project, 'after_insert')
async def create_initial_version(mapper, connection, project):
    """Create version 0 with template files when a project is created."""
    # Get session from mock in test or real session in production
    session = getattr(project, '_sa_session', None) or AsyncSession.object_session(project)
    
    if session is not None:
        try:
            # Create initial version
            version = Version(
                project_id=project.id,
                version_number=0,
                name="Initial Version"
            )
            session.add(version)
            await session.commit()  # Commit to get version.id
            await session.refresh(version)
            
            # Read and add template files
            template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'version-0')
            try:
                for root, _, files in os.walk(template_dir):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, template_dir)
                            
                            with open(file_path, 'r') as f:
                                content = f.read()
                            
                            file_obj = File(
                                version_id=version.id,
                                path=relative_path,
                                content=content
                            )
                            session.add(file_obj)
                        except IOError as e:
                            # Log error but continue with other files
                            print(f"Error reading file {file_path}: {e}")
                            continue
                
                await session.commit()  # Commit all file objects
            except Exception as e:
                # Log error but ensure version is still created
                print(f"Error creating template files: {e}")
                await session.rollback()
                # Commit version again in case it was rolled back
                await session.commit()
        except Exception as e:
            print(f"Error in create_initial_version: {e}")
            await session.rollback()
            raise
