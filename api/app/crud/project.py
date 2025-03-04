"""CRUD operations for projects using Supabase."""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from ..models.project import Project, ProjectCreate, ProjectUpdate
from ..models.base import dict_to_model
from ..services.supabase.client import get_supabase_client

class ProjectCRUD:
    """CRUD operations for projects using Supabase"""
    
    @staticmethod
    def get(project_id: UUID) -> Optional[Project]:
        """Get a project by ID"""
        client = get_supabase_client()
        
        # Query the projects table
        result = client.table("projects").select("*").eq("id", str(project_id)).execute()
        
        if not result.data:
            return None
        
        # Convert to Project model
        return dict_to_model(result.data[0], Project)

    @staticmethod
    def get_multi(skip: int = 0, limit: int = 100) -> List[Project]:
        """Get a list of active projects"""
        client = get_supabase_client()
        
        # Query for active projects with pagination
        result = client.table("projects") \
            .select("*") \
            .eq("is_active", True) \
            .order("created_at", desc=True) \
            .range(skip, skip + limit - 1) \
            .execute()
        
        # Convert to Project models
        return [dict_to_model(item, Project) for item in result.data]

    @staticmethod
    def create(project: ProjectCreate) -> Project:
        """Create a new project"""
        client = get_supabase_client()
        
        # Prepare data for insertion
        project_data = {
            "name": project.name,
            "description": project.description,
            "is_active": True
        }
        
        # Insert the project
        result = client.table("projects").insert(project_data).execute()
        
        if not result.data:
            raise ValueError("Failed to create project")
        
        # Convert to Project model
        return dict_to_model(result.data[0], Project)

    @staticmethod
    def update(project_id: UUID, project: ProjectUpdate) -> Optional[Project]:
        """Update a project"""
        client = get_supabase_client()
        
        # Extract fields to update
        update_data = project.model_dump(exclude_unset=True)
        if not update_data:
            return None
        
        # Ensure field name alignment with Supabase schema
        if "active" in update_data:
            update_data["is_active"] = update_data.pop("active")
        
        # Update the project
        result = client.table("projects") \
            .update(update_data) \
            .eq("id", str(project_id)) \
            .execute()
        
        if not result.data:
            return None
        
        # Convert to Project model
        return dict_to_model(result.data[0], Project)

    @staticmethod
    def delete(project_id: UUID) -> Optional[Project]:
        """Soft delete a project by setting is_active=False"""
        client = get_supabase_client()
        
        # Soft delete by updating is_active to False
        result = client.table("projects") \
            .update({"is_active": False}) \
            .eq("id", str(project_id)) \
            .execute()
        
        if not result.data:
            return None
        
        # Convert to Project model
        return dict_to_model(result.data[0], Project)
