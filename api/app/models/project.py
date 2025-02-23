"""
Project models module combining SQLAlchemy and Pydantic models.
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime, func, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import Field

from .base import Base, BaseSchema

# SQLAlchemy Models
class Project(Base):
    """SQLAlchemy model for projects."""
    __tablename__ = "projects"
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    @hybrid_property
    def latest_version_number(self) -> int:
        if self.versions:
            return max((version.version_number for version in self.versions), default=0)
        return 0

    @latest_version_number.expression
    def latest_version_number(cls):
        from .project import ProjectVersion
        return (
            select(func.max(ProjectVersion.version_number))
            .where(ProjectVersion.project_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    versions: Mapped[List["ProjectVersion"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )

class ProjectVersion(Base):
    """SQLAlchemy model for project versions."""
    __tablename__ = "project_versions"
    
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_version_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("project_versions.id"),
        nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    __table_args__ = (
        UniqueConstraint('project_id', 'version_number', name='uq_project_version'),
        CheckConstraint('version_number >= 0', name='ck_version_number_positive'),
    )
    
    def __init__(self, **kwargs):
        if 'version_number' in kwargs and kwargs['version_number'] < 0:
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError(
                statement="version_number validation",
                params={},
                orig=Exception("Version number cannot be negative")
            )
        super().__init__(**kwargs)
    
    # Relationships
    project: Mapped["Project"] = relationship(back_populates="versions")
    files: Mapped[List["File"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan"
    )

class File(Base):
    """SQLAlchemy model for files."""
    __tablename__ = "files"
    
    project_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("project_versions.id", ondelete="CASCADE")
    )
    path: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    __table_args__ = (
        CheckConstraint("length(path) > 0", name="ck_file_path_not_empty"),
        UniqueConstraint('project_version_id', 'path', name='unique_project_version_path'),
    )
    
    def __init__(self, **kwargs):
        if 'path' in kwargs and not kwargs['path']:
            raise ValueError("File path cannot be empty")
        if 'content' in kwargs and kwargs['content'] is None:
            raise ValueError("File content cannot be null")
        super().__init__(**kwargs)
    
    # Relationships
    version: Mapped["ProjectVersion"] = relationship(back_populates="files")

# Pydantic Schemas
from pydantic import Field, constr

class ProjectBase(BaseSchema):
    """Base schema for project data."""
    name: constr(min_length=1) = Field(..., description="The name of the project")
    description: str = Field("", description="Project description")

class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass

class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, description="The name of the project")
    description: Optional[str] = Field(None, description="Project description")
    active: Optional[bool] = Field(None, description="Whether the project is active")

class ProjectResponse(ProjectBase):
    """Schema for project responses."""
    id: UUID
    latest_version_number: int = Field(..., description="Latest version number")
    active: bool = Field(..., description="Whether the project is active")
    created_at: datetime
    updated_at: datetime

class ProjectVersionBase(BaseSchema):
    """Base schema for project version data."""
    version_number: int = Field(..., description="Version number", ge=0)
    name: str = Field("", description="Version name")
    parent_version_id: Optional[UUID] = Field(None, description="Parent version ID")

class ProjectVersionCreate(ProjectVersionBase):
    """Schema for creating a new project version."""
    project_id: UUID
    name: str = Field(default="", description="Version name")
    parent_version_id: Optional[UUID] = Field(None, description="Parent version ID")

class ProjectVersionListItem(BaseSchema):
    """Schema for project version list items.
    
    Used for the simplified list response when listing all versions of a project.
    Contains only essential identifying information. Active state is inherited from
    the parent project and not included in this simplified view.
    """
    id: UUID = Field(..., description="Version ID")
    version_number: int = Field(..., description="Sequential version number", ge=0)
    name: str = Field(..., description="Version name")

class FileResponse(BaseSchema):
    """Schema for file responses."""
    id: UUID = Field(..., description="File ID")
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")

class FileOperation(str, Enum):
    """Enum for file operations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class FileChange(BaseSchema):
    """Schema for file changes."""
    operation: FileOperation
    path: str = Field(..., description="Path of the file to operate on")
    content: Optional[str] = Field(None, description="Content for create/update operations")

class AIResponse(BaseSchema):
    """Schema for AI response containing file changes."""
    changes: List[FileChange] = Field(..., description="List of file changes to apply")

class CreateVersionRequest(BaseSchema):
    """Schema for creating a new version with changes."""
    name: str = Field(..., description="Required name for the version")
    parent_version_number: int = Field(..., ge=0, description="The version number to base the new version on")
    project_context: str = Field(..., description="Project context string")
    change_request: str = Field(..., description="Change request string")

class ProjectVersionResponse(ProjectVersionBase):
    """Schema for project version responses.
    
    Used for detailed version information when retrieving a specific version.
    Includes all version fields plus the parent's version number for easier traversal
    of the version history tree.
    """
    id: UUID
    project_id: UUID
    parent_version: Optional[int] = Field(None, description="The version number of the parent version (if any)")
    created_at: datetime
    updated_at: datetime
    files: List[FileResponse] = Field(default_factory=list, description="List of files associated with this version")
    active: bool = Field(..., description="Whether the version is active (inherited from project)")
