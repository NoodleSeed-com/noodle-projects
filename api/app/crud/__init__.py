"""CRUD operations for the application."""
from .project import ProjectCRUD
from .version import VersionCRUD
from .file import FileCRUD

# Export instances for easy access
projects = ProjectCRUD()
versions = VersionCRUD()
files = FileCRUD()

__all__ = ["projects", "versions", "files"]
