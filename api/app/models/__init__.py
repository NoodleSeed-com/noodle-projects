"""
Models for Supabase database operations.
"""
from .base import (
    BaseSchema,
    SupabaseResponse,
    PaginatedResponse,
    generate_uuid,
    dict_to_model,
    handle_supabase_response
)
from .file import (
    File,
    FileBase,
    FileCreate,
    FileUpdate,
    FileResponse,
    FileChange,
    FileOperation,
    AIResponse
)
from .version import (
    Version,
    VersionBase,
    VersionCreate,
    VersionResponse,
    VersionListItem,
    CreateVersionRequest
)
from .project import (
    Project,
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)

__all__ = [
    # Base utilities
    "BaseSchema",
    "SupabaseResponse",
    "PaginatedResponse",
    "generate_uuid",
    "dict_to_model",
    "handle_supabase_response",
    
    # File models
    "File",
    "FileBase",
    "FileCreate",
    "FileUpdate",
    "FileResponse", 
    "FileChange",
    "FileOperation",
    "AIResponse",
    
    # Version models
    "Version",
    "VersionBase",
    "VersionCreate",
    "VersionResponse",
    "VersionListItem",
    "CreateVersionRequest",
    
    # Project models
    "Project",
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
]
