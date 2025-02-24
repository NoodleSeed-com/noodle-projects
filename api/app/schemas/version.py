"""
Version API schemas for request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import Field

from .base import BaseSchema
from .file import FileResponse

class VersionBase(BaseSchema):
    """Base schema for version data."""
    version_number: int = Field(..., description="Version number", ge=0)
    name: str = Field("", description="Version name")
    parent_id: Optional[UUID] = Field(None, description="Parent version ID")

class VersionCreate(VersionBase):
    """Schema for creating a new version."""
    project_id: UUID
    name: str = Field(default="", description="Version name")
    parent_id: Optional[UUID] = Field(None, description="Parent version ID")

class VersionListItem(BaseSchema):
    """Schema for version list items.
    
    Used for the simplified list response when listing all versions of a project.
    Contains only essential identifying information. Active state is inherited from
    the parent project and not included in this simplified view.
    """
    id: UUID = Field(..., description="Version ID")
    version_number: int = Field(..., description="Sequential version number", ge=0)
    name: str = Field(..., description="Version name")

class VersionResponse(VersionBase):
    """Schema for version responses.
    
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

class CreateVersionRequest(BaseSchema):
    """Schema for creating a new version with changes."""
    name: str = Field(..., description="Required name for the version")
    parent_version_number: int = Field(..., ge=0, description="The version number to base the new version on")
    project_context: str = Field(..., description="Project context string")
    change_request: str = Field(..., description="Change request string")
