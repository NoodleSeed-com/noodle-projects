"""
Common schema types imported from app.models.file and app.models.base.
This file re-exports schemas to maintain backward compatibility.
"""
from app.models.file import FileOperation, FileChange, AIResponse
from app.models.base import PaginatedResponse

# Original schema names for backward compatibility
__all__ = [
    "FileOperation",
    "FileChange", 
    "AIResponse",
    "PaginatedResponse"
]
