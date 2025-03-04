"""
Project model with Pydantic v2 schemas for validation and serialization.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4

from pydantic import Field, field_validator, computed_field, model_validator

from .base import BaseSchema

class ProjectBase(BaseSchema):
    """Base model for all project-related schemas."""
    name: str = Field(..., description="The name of the project", min_length=1, max_length=255)
    description: str = Field("", description="Project description")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Validate project name is not empty and within length limits."""
        if not v:
            raise ValueError("Project name cannot be empty")
        if len(v) > 255:
            raise ValueError("Project name cannot exceed 255 characters")
        return v

class Project(ProjectBase):
    """Project model using Pydantic v2."""
    id: UUID
    is_active: bool = Field(True, description="Whether the project is active")
    created_at: datetime
    updated_at: datetime
    
    # Note: This won't be populated by default from Supabase
    # It will be populated separately when needed
    versions: Optional[List[Dict[str, Any]]] = None
    
    def latest_version_number(self) -> int:
        """Get the latest version number from loaded versions."""
        if not self.versions:
            return 0
        return max((v.get("version_number", 0) for v in self.versions), default=0)

class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass

class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, description="The name of the project")
    description: Optional[str] = Field(None, description="Project description")
    is_active: Optional[bool] = Field(None, description="Whether the project is active", alias="active")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name field if provided."""
        if v is not None:
            if not v:
                raise ValueError("Project name cannot be empty")
            if len(v) > 255:
                raise ValueError("Project name cannot exceed 255 characters")
        return v
    
    @model_validator(mode='before')
    @classmethod
    def check_empty_update(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure at least one field is provided for update."""
        if isinstance(data, dict) and not any(k in data for k in ['name', 'description', 'is_active', 'active']):
            raise ValueError("At least one field must be provided for update")
        return data

class ProjectResponse(ProjectBase):
    """Schema for project responses in the API."""
    id: UUID
    is_active: bool = Field(..., description="Whether the project is active", alias="active")
    created_at: datetime
    updated_at: datetime
    latest_version_number: int = Field(0, description="Latest version number")
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Sample Project",
                "description": "A sample project description",
                "active": True,
                "latest_version_number": 3,
                "created_at": "2024-02-22T12:00:00Z",
                "updated_at": "2024-02-22T12:00:00Z"
            }
        }
    }
