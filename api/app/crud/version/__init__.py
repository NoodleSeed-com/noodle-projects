"""Version CRUD package."""
from uuid import UUID

from .crud import (
    get_version,
    get_versions,
    create_version,
    get_next_version_number
)
from .template import create_initial_version
from .file_operations import validate_file_changes, apply_file_changes

__all__ = [
    'get_version',
    'get_versions', 
    'create_version',
    'create_initial_version',
    'get_next_version_number',
    'validate_file_changes',
    'apply_file_changes'
]
