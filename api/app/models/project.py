"""
Project database model.
"""
from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class Project(Base):
    """SQLAlchemy model for projects."""
    __tablename__ = "projects"
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Relationships with explicit loading strategy
    versions: Mapped[List["Version"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"  # Use selectin loading to avoid async issues
    )

    def __init__(self, **kwargs):
        if 'name' in kwargs:
            if not kwargs['name']:
                raise ValueError("Project name cannot be empty")
            if len(kwargs['name']) > 255:
                raise ValueError("Project name cannot exceed 255 characters")
        super().__init__(**kwargs)

    @property
    def latest_version_number(self) -> int:
        """Get the latest version number from loaded versions."""
        return max((v.version_number for v in self.versions), default=0)
