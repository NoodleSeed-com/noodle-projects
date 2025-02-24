"""
File API schemas for request/response validation.
"""
from uuid import UUID
from pydantic import Field

from .base import BaseSchema
from .common import FileOperation

class FileResponse(BaseSchema):
    """Schema for file responses."""
    id: UUID = Field(..., description="File ID")
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
