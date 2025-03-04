"""
File API schemas imported from app.models.file.
This file re-exports schemas to maintain backward compatibility.
"""
from app.models.file import (
    FileOperation,
    FileBase,
    File,
    FileCreate,
    FileUpdate,
    FileResponse,
    FileChange
)

# Original schema names for backward compatibility
__all__ = [
    "FileOperation",
    "FileBase",
    "File",
    "FileCreate", 
    "FileUpdate",
    "FileResponse",
    "FileChange"
]
