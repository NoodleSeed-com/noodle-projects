"""
Consolidated file operations package.
"""
from .crud import FileCRUD
from .operations import validate_file_changes, apply_file_changes

__all__ = ["FileCRUD", "validate_file_changes", "apply_file_changes"]