"""
Version database model.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.exc import IntegrityError

from .base import Base

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
        if 'version_number' in kwargs and kwargs['version_number'] < 0:
            raise IntegrityError(
                statement="version_number validation",
                params={},
                orig=Exception("Version number cannot be negative")
            )
        super().__init__(**kwargs)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="versions")
    files: Mapped[List["File"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def active(self) -> bool:
        """Whether this version is active (inherited from project)."""
        return self.project.active
