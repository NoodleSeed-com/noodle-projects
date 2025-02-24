"""API route handlers."""
from fastapi import APIRouter
from .projects import router as projects_router
from .versions import router as versions_router

# Create main router
router = APIRouter()

# Include sub-routers with prefixes
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(
    versions_router,
    prefix="/projects/{project_id}/versions",
    tags=["versions"]
)
