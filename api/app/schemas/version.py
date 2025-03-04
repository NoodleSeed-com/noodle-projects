"""
Version API schemas imported from app.models.version.
This file re-exports schemas to maintain backward compatibility.
"""
from app.models.version import (
    VersionBase,
    Version,
    VersionCreate,
    VersionListItem,
    VersionResponse,
    CreateVersionRequest
)

# Original schema names for backward compatibility
__all__ = [
    "VersionBase",
    "Version",
    "VersionCreate",
    "VersionListItem",
    "VersionResponse", 
    "CreateVersionRequest"
]
