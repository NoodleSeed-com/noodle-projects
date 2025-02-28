"""
File database model.
"""
from uuid import UUID
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class File(Base):
    """SQLAlchemy model for files."""
    __tablename__ = "files"
    
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("versions.id", ondelete="CASCADE")
    )
    path: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('version_id', 'path', name='unique_version_path'),
    )
    
    def __init__(self, **kwargs):
        if 'version_id' not in kwargs:
            raise ValueError("version_id is required")
        if 'path' in kwargs:
            if not kwargs['path']:
                raise ValueError("File path cannot be empty")
            if len(kwargs['path']) > 1024:
                raise ValueError("File path cannot exceed 1024 characters")
        if 'content' in kwargs and kwargs['content'] is None:
            raise ValueError("File content cannot be null")
        super().__init__(**kwargs)
    
    # Relationships
    version: Mapped["Version"] = relationship("Version", back_populates="files")
