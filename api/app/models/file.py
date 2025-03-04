"""
File model definitions for database storage and API operations.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import Field, field_validator

from .base import BaseSchema

class FileOperation(str, Enum):
    """Enum for file operations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class FileBase(BaseSchema):
    """Base schema with common file attributes."""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate file path is not empty and properly formatted."""
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        if len(v.strip()) > 1024:
            raise ValueError("File path cannot exceed 1024 characters")
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate file content is not empty."""
        if v is None:
            raise ValueError("File content cannot be null")
        return v

class File(FileBase):
    """Complete file model with all attributes."""
    id: UUID
    version_id: UUID = Field(..., description="ID of the version this file belongs to")
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "version_id": "123e4567-e89b-12d3-a456-426614174001",
                "path": "src/App.tsx",
                "content": "console.log('Hello World');",
                "created_at": "2024-02-22T12:00:00Z",
                "updated_at": "2024-02-22T12:00:00Z"
            }
        }
    }

class FileCreate(FileBase):
    """Schema for file creation requests."""
    version_id: UUID = Field(..., description="Version ID this file belongs to")
    operation: FileOperation = Field(FileOperation.CREATE, description="File operation")

class FileUpdate(FileBase):
    """Schema for file update requests."""
    operation: FileOperation = Field(FileOperation.UPDATE, description="File operation")

class FileResponse(FileBase):
    """Schema for file responses."""
    id: UUID = Field(..., description="File ID")
    version_id: UUID = Field(..., description="Version ID this file belongs to")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class FileChange(BaseSchema):
    """Schema for file changes when performing batch operations."""
    operation: FileOperation
    path: str = Field(..., description="Path of the file to operate on")
    content: Optional[str] = Field(None, description="Content for create/update operations")

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate file path is not empty."""
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str], info) -> Optional[str]:
        """Validate content is provided for CREATE and UPDATE operations."""
        if info.data.get('operation') in (FileOperation.CREATE, FileOperation.UPDATE) and v is None:
            raise ValueError(f"Content required for {info.data.get('operation')} operation")
        return v

class AIResponse(BaseSchema):
    """Schema for AI response containing file changes."""
    changes: List[FileChange] = Field(..., description="List of file changes to apply")
