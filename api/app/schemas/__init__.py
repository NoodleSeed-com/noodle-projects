"""
API schema models using Pydantic for request/response validation.
"""
from .project import ProjectBase, ProjectCreate, ProjectUpdate, ProjectResponse
from .version import (
    VersionBase, VersionCreate, VersionResponse,
    VersionListItem, CreateVersionRequest
)
from .file import FileResponse
from .common import AIResponse, FileChange, FileOperation

__all__ = [
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "VersionBase",
    "VersionCreate",
    "VersionResponse",
    "VersionListItem",
    "CreateVersionRequest",
    "FileResponse",
    "FileChange",
    "FileOperation",
    "AIResponse",
]
