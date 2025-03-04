"""
Version model and schemas with integrated Pydantic validation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Type, ClassVar
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from .base import BaseSchema
from ..errors import NoodleError, ErrorType

class VersionBase(BaseSchema):
    """Base schema for version data."""
    version_number: int = Field(..., description="Version number", ge=0)
    name: str = Field("", description="Version name")
    parent_id: Optional[UUID] = Field(None, description="Parent version ID")

    @field_validator('version_number')
    @classmethod
    def validate_version_number(cls, v: int) -> int:
        """Validate version number is not negative."""
        if v < 0:
            raise ValueError("Version number cannot be negative")
        return v


class Version(VersionBase):
    """
    Version model using Pydantic v2.
    
    A version represents a point-in-time state of a project's files.
    Each version has a sequential version number and can reference a parent version
    from which it was created.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    project_id: UUID = Field(..., description="Project ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Optional fields populated from relationships
    files: Optional[List["File"]] = Field(None, description="List of files in this version")
    parent_version: Optional[int] = Field(None, description="The version number of the parent version")
    active: Optional[bool] = Field(None, description="Whether the version is active (inherited from project)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "project_id": "123e4567-e89b-12d3-a456-426614174001",
                "version_number": 1,
                "name": "Initial version",
                "parent_id": None,
                "created_at": "2024-02-22T12:00:00Z",
                "updated_at": "2024-02-22T12:00:00Z",
                "active": True
            }
        }
    }
    
    @model_validator(mode='after')
    def validate_model(self) -> 'Version':
        """Validate project_id is provided."""
        if not self.project_id:
            raise ValueError("project_id is required")
        return self
    
    def is_active(self, project_active: bool) -> bool:
        """Determine if version is active based on project status."""
        # In this model, active state is inherited from project
        return project_active


class VersionCreate(BaseSchema):
    """Schema for creating a new version."""
    project_id: UUID
    name: str = Field(default="", description="Version name")
    parent_id: Optional[UUID] = Field(None, description="Parent version ID")
    version_number: Optional[int] = Field(None, description="Version number (optional, auto-assigned if not provided)")

    @field_validator('version_number')
    @classmethod
    def validate_version_number(cls, v: Optional[int]) -> Optional[int]:
        """Validate version number if provided."""
        if v is not None and v < 0:
            raise ValueError("Version number cannot be negative")
        return v


class VersionListItem(BaseSchema):
    """Schema for version list items.
    
    Used for the simplified list response when listing all versions of a project.
    """
    id: UUID = Field(..., description="Version ID")
    version_number: int = Field(..., description="Sequential version number", ge=0)
    name: str = Field(..., description="Version name")


class VersionResponse(VersionBase):
    """Schema for version responses.
    
    Used for detailed version information when retrieving a specific version.
    """
    id: UUID
    project_id: UUID
    parent_version: Optional[int] = Field(None, description="The version number of the parent version (if any)")
    created_at: datetime
    updated_at: datetime
    files: List["FileResponse"] = Field(default_factory=list, description="List of files associated with this version")
    active: bool = Field(..., description="Whether the version is active (inherited from project)")


class CreateVersionRequest(BaseSchema):
    """Schema for creating a new version with changes."""
    name: str = Field(..., description="Required name for the version")
    parent_version_number: int = Field(..., ge=0, description="The version number to base the new version on")
    project_context: str = Field(..., description="Project context string")
    change_request: str = Field(..., description="Change request string")


# To avoid circular imports, these imports are at the end
from .file import File, FileResponse
