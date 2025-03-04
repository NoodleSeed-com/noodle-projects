"""
API schema models using Pydantic for request/response validation.
All schemas are now defined in the app.models package.
This package re-exports models from app.models for backward compatibility.
"""
from .base import BaseSchema
from .project import (
    ProjectBase, 
    Project,
    ProjectCreate, 
    ProjectUpdate, 
    ProjectResponse
)
from .version import (
    Version,
    VersionBase, 
    VersionCreate, 
    VersionResponse,
    VersionListItem, 
    CreateVersionRequest
)
from .file import (
    File,
    FileBase,
    FileCreate,
    FileUpdate,
    FileResponse
)
from .common import (
    AIResponse, 
    FileChange, 
    FileOperation,
    PaginatedResponse
)

__all__ = [
    # Base
    "BaseSchema",
    
    # Project schemas
    "ProjectBase",
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    
    # Version schemas
    "Version",
    "VersionBase",
    "VersionCreate",
    "VersionResponse",
    "VersionListItem",
    "CreateVersionRequest",
    
    # File schemas
    "File",
    "FileBase",
    "FileCreate",
    "FileUpdate",
    "FileResponse",
    
    # Common schema types
    "FileChange",
    "FileOperation",
    "AIResponse",
    "PaginatedResponse",
]
