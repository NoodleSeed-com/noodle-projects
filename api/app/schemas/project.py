"""
Project API schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import Field, constr

from .base import BaseSchema

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
