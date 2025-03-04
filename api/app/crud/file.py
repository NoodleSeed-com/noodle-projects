"""CRUD operations for files using Supabase."""
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..models.base import dict_to_model
from ..models.file import FileResponse
from ..services.supabase.client import get_supabase_client

class FileCRUD:
    """CRUD operations for files using Supabase"""
    
    @staticmethod
    def get_by_version(
        version_id: UUID
    ) -> List[FileResponse]:
        """Get all files for a specific version."""
        client = get_supabase_client()
        
        result = client.table("files") \
            .select("*") \
            .eq("version_id", str(version_id)) \
            .execute()
            
        return [
            FileResponse(
                id=file["id"],
                path=file["path"],
                content=file["content"]
            ) for file in result.data
        ]

    @staticmethod
    def get_by_path(
        version_id: UUID,
        path: str
    ) -> Optional[FileResponse]:
        """Get a specific file by its path within a version."""
        client = get_supabase_client()
        
        result = client.table("files") \
            .select("*") \
            .eq("version_id", str(version_id)) \
            .eq("path", path) \
            .execute()
            
        if not result.data:
            return None
            
        file = result.data[0]
        return FileResponse(
            id=file["id"],
            path=file["path"],
            content=file["content"]
        )
