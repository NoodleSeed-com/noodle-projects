"""
Version database model.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, CheckConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship, object_session, Session
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy.orm.session import object_session

from .base import Base
from .file import File
from .project import Project
from ..errors import NoodleError, ErrorType

class Version(Base):
    """SQLAlchemy model for versions.
    
    A version represents a point-in-time state of a project's files.
    Each version has a sequential version number and can reference a parent version
    from which it was created.
    """
    __tablename__ = "versions"
    
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("versions.id"),
        nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False, default="")
    
    __table_args__ = (
        UniqueConstraint('project_id', 'version_number', name='uq_version'),
        CheckConstraint('version_number >= 0', name='ck_version_number_positive'),
    )
    
    def __init__(self, **kwargs):
        # Required field validation
        if 'project_id' not in kwargs:
            raise NoodleError("project_id is required")
            
        # Default version_number to 0 if not provided
        if 'version_number' not in kwargs:
            kwargs['version_number'] = 0
            
        # Python-level validation for version_number
        if kwargs['version_number'] < 0:
            raise NoodleError("Version number cannot be negative")
            
        # Get session for validation
        session = kwargs.pop('session', None)
            
        # Store project_id for validation
        self.project_id = kwargs['project_id']
            
        # Initialize to set up relationships
        super().__init__(**kwargs)

        # Validate if we have a session
        if session or (session := object_session(self)):
            self.validate(session)

    def validate(self, session):
        """Validate version state."""
        project = session.get(Project, self.project_id)
        if not project or not project.active:
            raise NoodleError("Cannot create version in inactive project")
            
        # Validate parent version is from same project
        if self.parent_id:
            parent = session.get(Version, self.parent_id)
            if parent and parent.project_id != self.project_id:
                raise NoodleError(
                    "Parent version must be from the same project",
                    error_type=ErrorType.VALIDATION
                )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="versions")
    files: Mapped[List["File"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="File.path"
    )

    @hybrid_property
    def active(self) -> bool:
        """Whether this version is active (inherited from project)."""
        return self.project.active

@event.listens_for(Session, "before_commit")
def validate_version_before_commit(session):
    """Validate version creation before commit."""
    for obj in session.new:
        if isinstance(obj, Version):
            obj.validate(session)
