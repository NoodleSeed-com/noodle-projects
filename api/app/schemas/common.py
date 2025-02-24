"""
Common schema types and enums shared across API schemas.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class FileOperation(str, Enum):
    """Enum for file operations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class FileChange(BaseModel):
    """Schema for file changes."""
    operation: FileOperation
    path: str = Field(..., description="Path of the file to operate on")
    content: Optional[str] = Field(None, description="Content for create/update operations")

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str], info) -> Optional[str]:
        if info.data.get('operation') in (FileOperation.CREATE, FileOperation.UPDATE) and not v:
            raise ValueError(f"Content required for {info.data.get('operation')} operation")
        return v

class AIResponse(BaseModel):
    """Schema for AI response containing file changes."""
    changes: List[FileChange] = Field(..., description="List of file changes to apply")
