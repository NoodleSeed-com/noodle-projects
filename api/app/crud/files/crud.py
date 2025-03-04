"""
CRUD operations for files using Supabase client.
"""
from typing import Optional, List, Dict
from uuid import UUID

from app.models.file import File, FileResponse
from app.errors import NoodleError, ErrorType
from app.services.supabase.client import get_supabase_client

class FileCRUD:
    """CRUD operations for files using Supabase."""
    
    @staticmethod
    def get_by_version(
        version_id: UUID
    ) -> List[FileResponse]:
        """Get all files for a specific version.
        
        Args:
            version_id: UUID of the version
            
        Returns:
            List of file response objects
        """
        client = get_supabase_client()
        response = client.table("files") \
            .select("*") \
            .eq("version_id", str(version_id)) \
            .execute()
            
        if not response.data:
            return []
            
        return [
            FileResponse(
                id=file["id"],
                version_id=file["version_id"],
                path=file["path"],
                content=file["content"],
                created_at=file["created_at"],
                updated_at=file["updated_at"]
            ) for file in response.data
        ]
    
    @staticmethod
    def get_by_path(
        version_id: UUID,
        path: str
    ) -> Optional[FileResponse]:
        """Get a specific file by its path within a version.
        
        Args:
            version_id: UUID of the version
            path: File path
            
        Returns:
            File response object or None if not found
        """
        client = get_supabase_client()
        response = client.table("files") \
            .select("*") \
            .eq("version_id", str(version_id)) \
            .eq("path", path) \
            .execute()
            
        if not response.data:
            return None
            
        file = response.data[0]
        return FileResponse(
            id=file["id"],
            version_id=file["version_id"],
            path=file["path"],
            content=file["content"],
            created_at=file["created_at"],
            updated_at=file["updated_at"]
        )
    
    @staticmethod
    def create_file(
        version_id: UUID,
        path: str,
        content: str
    ) -> FileResponse:
        """Create a new file.
        
        Args:
            version_id: UUID of the version
            path: File path
            content: File content
            
        Returns:
            Created file response object
        """
        # Check if file already exists
        existing_file = FileCRUD.get_by_path(version_id, path)
        if existing_file:
            raise NoodleError(
                f"File already exists at path '{path}' in version {version_id}",
                ErrorType.CONFLICT
            )
        
        # Create new file
        client = get_supabase_client()
        file_data = {
            "version_id": str(version_id),
            "path": path,
            "content": content
        }
        
        response = client.table("files").insert(file_data).execute()
        
        if not response.data:
            raise NoodleError(
                "Failed to create file in database",
                ErrorType.DATABASE
            )
            
        file = response.data[0]
        return FileResponse(
            id=file["id"],
            version_id=file["version_id"],
            path=file["path"],
            content=file["content"],
            created_at=file["created_at"],
            updated_at=file["updated_at"]
        )
    
    @staticmethod
    def update_content(
        file_id: UUID,
        content: str
    ) -> FileResponse:
        """Update a file's content.
        
        Args:
            file_id: UUID of the file
            content: New file content
            
        Returns:
            Updated file response object
        """
        client = get_supabase_client()
        
        # Check if file exists
        response = client.table("files") \
            .select("*") \
            .eq("id", str(file_id)) \
            .execute()
            
        if not response.data:
            raise NoodleError(
                f"File with ID {file_id} not found",
                ErrorType.NOT_FOUND
            )
        
        # Update file content
        update_response = client.table("files") \
            .update({"content": content}) \
            .eq("id", str(file_id)) \
            .execute()
            
        if not update_response.data:
            raise NoodleError(
                "Failed to update file in database",
                ErrorType.DATABASE
            )
            
        file = update_response.data[0]
        return FileResponse(
            id=file["id"],
            version_id=file["version_id"],
            path=file["path"],
            content=file["content"],
            created_at=file["created_at"],
            updated_at=file["updated_at"]
        )
    
    @staticmethod
    def delete_file(
        file_id: UUID
    ) -> None:
        """Delete a file.
        
        Args:
            file_id: UUID of the file
        """
        client = get_supabase_client()
        
        # Check if file exists
        response = client.table("files") \
            .select("*") \
            .eq("id", str(file_id)) \
            .execute()
            
        if not response.data:
            raise NoodleError(
                f"File with ID {file_id} not found",
                ErrorType.NOT_FOUND
            )
        
        # Delete file
        delete_response = client.table("files") \
            .delete() \
            .eq("id", str(file_id)) \
            .execute()
            
        if not delete_response.data:
            raise NoodleError(
                "Failed to delete file from database",
                ErrorType.DATABASE
            )
    
    @staticmethod
    def get_files_dict(
        version_id: UUID
    ) -> Dict[str, File]:
        """Get all files for a version as a dictionary keyed by path.
        
        Args:
            version_id: UUID of the version
            
        Returns:
            Dictionary of files keyed by path
        """
        client = get_supabase_client()
        response = client.table("files") \
            .select("*") \
            .eq("version_id", str(version_id)) \
            .execute()
            
        if not response.data:
            return {}
            
        files = [
            File(
                id=file["id"],
                version_id=file["version_id"],
                path=file["path"],
                content=file["content"],
                created_at=file["created_at"],
                updated_at=file["updated_at"]
            ) for file in response.data
        ]
        
        return {file.path: file for file in files}