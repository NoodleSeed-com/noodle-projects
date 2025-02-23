import os
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from .models.project import (
    Project,
    ProjectVersion,
    File,
    ProjectCreate,
    ProjectUpdate,
    ProjectVersionListItem,
    ProjectVersionResponse,
    FileResponse,
    FileOperation,
    FileChange
)

class ProjectCRUD:
    """CRUD operations for projects"""
    
    @staticmethod
    def get(db: Session, project_id: UUID) -> Optional[Project]:
        """Get a project by ID"""
        result = db.execute(select(Project).filter(Project.id == project_id))
        return result.scalar_one_or_none()

    @staticmethod
    def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get a list of active projects"""
        result = db.execute(
            select(Project)
            .filter(Project.active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    def create(db: Session, project: ProjectCreate) -> Project:
        """Create a new project"""
        db_project = Project(
            name=project.name,
            description=project.description
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        # Create initial version with template files
        db_version = ProjectVersion(
            project_id=db_project.id,
            version_number=0,
            name="Initial Version"
        )
        db.add(db_version)
        db.commit()
        db.refresh(db_version)

        # Read and add template files
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'version-0')
        for root, _, files in os.walk(template_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, template_dir)
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                db_file = File(
                    project_version_id=db_version.id,
                    path=relative_path,
                    content=content
                )
                db.add(db_file)
        
        db.commit()
        return db_project

    @staticmethod
    def update(db: Session, project_id: UUID, project: ProjectUpdate) -> Optional[Project]:
        """Update a project"""
        update_data = project.model_dump(exclude_unset=True)
        if not update_data:
            return None
            
        stmt = update(Project).where(Project.id == project_id).values(**update_data).returning(Project)
        result = db.execute(stmt)
        db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    def delete(db: Session, project_id: UUID) -> Optional[Project]:
        """Soft delete a project by setting active=False"""
        stmt = update(Project).where(Project.id == project_id).values(active=False).returning(Project)
        result = db.execute(stmt)
        db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    def get_version(db: Session, project_id: UUID, version_number: int) -> Optional[ProjectVersionResponse]:
        """Get a specific version of a project including its files"""
        # Get the version with files eagerly loaded
        version = db.execute(
            select(ProjectVersion)
            .options(joinedload(ProjectVersion.files))  # Eager load files
            .filter(
                ProjectVersion.project_id == project_id,
                ProjectVersion.version_number == version_number
            )
        ).unique().scalar_one_or_none()
        
        if not version:
            return None

        # Get parent version number if it exists
        parent_version = None
        if version.parent_version_id:
            parent_version = db.execute(
                select(ProjectVersion.version_number)
                .filter(ProjectVersion.id == version.parent_version_id)
            ).scalar_one_or_none()

        # Convert files to FileResponse objects
        file_responses = [
            FileResponse(
                id=file.id,
                path=file.path,
                content=file.content
            ) for file in version.files
        ]
        
        # Create and return a ProjectVersionResponse
        return ProjectVersionResponse(
            id=version.id,
            project_id=version.project_id,
            version_number=version.version_number,
            name=version.name,
            parent_version_id=version.parent_version_id,
            parent_version=parent_version,
            created_at=version.created_at,
            updated_at=version.updated_at,
            files=file_responses
        )

    @staticmethod
    def get_versions(db: Session, project_id: UUID, skip: int = 0, limit: int = 100) -> List[ProjectVersionListItem]:
        """Get all versions of a project"""
        result = db.execute(
            select(ProjectVersion.id, ProjectVersion.version_number, ProjectVersion.name)
            .filter(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number)
            .offset(skip)
            .limit(limit)
        )
        return [ProjectVersionListItem(id=id, version_number=number, name=name) 
                for id, number, name in result]

    @staticmethod
    def create_version(
        db: Session,
        project_id: UUID,
        parent_version_number: int,
        name: str,
        changes: List[FileChange]
    ) -> Optional[ProjectVersionResponse]:
        """Create a new version based on a parent version and apply changes.
        
        Args:
            db: Database session
            project_id: Project UUID
            parent_version_number: Version number to base the new version on
            name: Name for the new version
            changes: List of file changes to apply
            
        Returns:
            New version with applied changes, or None if parent version not found
        """
        # Get parent version with its files
        parent_version = db.execute(
            select(ProjectVersion)
            .options(joinedload(ProjectVersion.files))
            .filter(
                ProjectVersion.project_id == project_id,
                ProjectVersion.version_number == parent_version_number
            )
        ).unique().scalar_one_or_none()
        
        if not parent_version:
            return None
            
        # Create new version with incremented version number
        new_version = ProjectVersion(
            project_id=project_id,
            version_number=parent_version.version_number + 1,
            parent_version_id=parent_version.id,
            name=name
        )
        db.add(new_version)
        db.flush()  # Get new_version.id without committing
        
        # Create a map of existing files by path
        existing_files = {file.path: file for file in parent_version.files}
        
        # Create list to track all files for the new version
        files_to_add = []
        
        # First copy all files from parent version
        for path, file in existing_files.items():
            files_to_add.append(File(
                project_version_id=new_version.id,
                path=path,
                content=file.content
            ))
        
        # Apply changes
        for change in changes:
            if change.operation == FileOperation.CREATE:
                if not change.content:
                    raise ValueError(f"Content required for CREATE operation on {change.path}")
                files_to_add.append(File(
                    project_version_id=new_version.id,
                    path=change.path,
                    content=change.content
                ))
            
            elif change.operation == FileOperation.UPDATE:
                if not change.content:
                    raise ValueError(f"Content required for UPDATE operation on {change.path}")
                if change.path not in existing_files:
                    raise ValueError(f"Cannot update non-existent file: {change.path}")
                # Remove old file if it exists
                files_to_add = [f for f in files_to_add if f.path != change.path]
                # Add updated file
                files_to_add.append(File(
                    project_version_id=new_version.id,
                    path=change.path,
                    content=change.content
                ))
            
            elif change.operation == FileOperation.DELETE:
                if change.path not in existing_files:
                    raise ValueError(f"Cannot delete non-existent file: {change.path}")
                # Remove file from list
                files_to_add = [f for f in files_to_add if f.path != change.path]
        
        # Set the files relationship and commit
        new_version.files = files_to_add
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        
        # Return the complete version response
        return ProjectCRUD.get_version(db, project_id, new_version.version_number)

# Export the CRUD operations
projects = ProjectCRUD()
