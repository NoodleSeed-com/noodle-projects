"""CRUD operations for projects."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.project import Project
from ..models.version import Version
from ..schemas.project import ProjectCreate, ProjectUpdate

class ProjectCRUD:
    """CRUD operations for projects"""
    
    @staticmethod
    async def get(db: AsyncSession, project_id: UUID) -> Optional[Project]:
        """Get a project by ID"""
        result = await db.execute(
            select(Project)
            .options(joinedload(Project.versions))
            .filter(Project.id == project_id)
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get a list of active projects"""
        result = await db.execute(
            select(Project)
            .filter(Project.active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, project: ProjectCreate) -> Project:
        """Create a new project"""
        db_project = Project(
            name=project.name,
            description=project.description
        )
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        return db_project

    @staticmethod
    async def update(db: AsyncSession, project_id: UUID, project: ProjectUpdate) -> Optional[Project]:
        """Update a project"""
        update_data = project.model_dump(exclude_unset=True)
        if not update_data:
            return None
            
        stmt = update(Project).where(Project.id == project_id).values(**update_data).returning(Project)
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, project_id: UUID) -> Optional[Project]:
        """Soft delete a project by setting active=False"""
        stmt = update(Project).where(Project.id == project_id).values(active=False).returning(Project)
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()
