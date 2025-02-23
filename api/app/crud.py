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
    FileResponse
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

        # Create initial version
        db_version = ProjectVersion(
            project_id=db_project.id,
            version_number=0,
            name="Initial Version"
        )
        db.add(db_version)
        db.commit()
        db.refresh(db_version)

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

# Export the CRUD operations
projects = ProjectCRUD()
