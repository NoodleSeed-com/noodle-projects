"""
Project API schemas imported from app.models.project.
This file re-exports schemas to maintain backward compatibility.
"""
from app.models.project import (
    ProjectBase,
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)

# Original schema names for backward compatibility
__all__ = [
    "ProjectBase",
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse"
]
