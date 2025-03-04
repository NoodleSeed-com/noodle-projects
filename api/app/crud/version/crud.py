"""Core CRUD operations for project versions using Supabase."""
from typing import Optional, List, Dict, Any
from uuid import UUID

from ...models.version import VersionResponse, VersionListItem
from ...models.file import FileResponse, FileChange
from ...models.base import dict_to_model
from ...services.supabase.client import get_supabase_client
from .template import create_initial_version

class VersionCRUD:
    """CRUD operations for versions using Supabase"""
    
    @staticmethod
    def create_initial_version(project_id: UUID) -> Dict[str, Any]:
        """Create version 0 with template files for a new project.
        
        Args:
            project_id: Project UUID
            
        Returns:
            Created initial version
        """
        return create_initial_version(project_id)
    
    @staticmethod
    def get_version(project_id: UUID, version_number: int) -> Optional[VersionResponse]:
        """Get a specific version of a project.
        
        This is an alias for the get() method to maintain consistency with route naming.
        
        Args:
            project_id: Project UUID
            version_number: Version number
            
        Returns:
            Version response or None if not found
        """
        return VersionCRUD.get(project_id, version_number)
    
    @staticmethod
    def get_versions(project_id: UUID, skip: int = 0, limit: int = 100) -> List[VersionListItem]:
        """Get all versions of a project.
        
        This is an alias for the get_multi() method to maintain consistency with route naming.
        
        Args:
            project_id: Project UUID
            skip: Number of versions to skip
            limit: Maximum number of versions to return
            
        Returns:
            List of version list items
        """
        return VersionCRUD.get_multi(project_id, skip, limit)
    
    @staticmethod
    def get_next_number(project_id: UUID) -> int:
        """Get the next available version number for a project.
        
        Args:
            project_id: Project UUID
            
        Returns:
            Next available version number (always >= 1, since 0 is reserved for initial version)
        """
        client = get_supabase_client()
        
        # Get versions ordered by version_number in descending order
        result = client.table("versions") \
            .select("version_number") \
            .eq("project_id", str(project_id)) \
            .order("version_number", desc=True) \
            .limit(1) \
            .execute()
            
        # Get latest version number
        latest_version = result.data[0]["version_number"] if result.data else 0
        next_number = latest_version + 1
        
        # Ensure we never return 0, as it's reserved for the initial version
        return max(1, next_number)

    @staticmethod
    def get(
        project_id: UUID,
        version_number: int
    ) -> Optional[VersionResponse]:
        """Get a specific version of a project including its files."""
        client = get_supabase_client()
        
        # Get the version
        version_result = client.table("versions") \
            .select("*") \
            .eq("project_id", str(project_id)) \
            .eq("version_number", version_number) \
            .execute()
            
        if not version_result.data:
            return None
            
        version = version_result.data[0]
        
        # Get parent version number if it exists
        parent_version = None
        if version.get("parent_id"):
            parent_result = client.table("versions") \
                .select("version_number") \
                .eq("id", version["parent_id"]) \
                .execute()
                
            if parent_result.data:
                parent_version = parent_result.data[0]["version_number"]
        
        # Get project's active state
        project_result = client.table("projects") \
            .select("is_active") \
            .eq("id", str(project_id)) \
            .execute()
            
        project_active = project_result.data[0]["is_active"] if project_result.data else False
        
        # Get files for this version
        files_result = client.table("files") \
            .select("*") \
            .eq("version_id", version["id"]) \
            .execute()
            
        # Convert to FileResponse objects
        file_responses = [
            FileResponse(
                id=file["id"],
                path=file["path"],
                content=file["content"]
            ) for file in files_result.data
        ]
        
        # Create and return the version response
        return VersionResponse(
            id=version["id"],
            project_id=version["project_id"],
            version_number=version["version_number"],
            name=version["name"],
            parent_id=version.get("parent_id"),
            parent_version=parent_version,
            created_at=version["created_at"],
            updated_at=version["updated_at"],
            files=file_responses,
            active=project_active
        )

    @staticmethod
    def get_multi(
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[VersionListItem]:
        """Get all versions of a project.
        
        Only returns versions if the project is active.
        """
        client = get_supabase_client()
        
        # First check if project is active
        project_result = client.table("projects") \
            .select("is_active") \
            .eq("id", str(project_id)) \
            .execute()
            
        project_active = project_result.data[0]["is_active"] if project_result.data else False
        
        # Return empty list if project is inactive
        if not project_active:
            return []
        
        # Get versions with pagination
        result = client.table("versions") \
            .select("id, version_number, name") \
            .eq("project_id", str(project_id)) \
            .order("version_number") \
            .range(skip, skip + limit - 1) \
            .execute()
            
        return [
            VersionListItem(
                id=row["id"],
                version_number=row["version_number"],
                name=row["name"]
            ) for row in result.data
        ]

    @staticmethod
    def create_version(
        project_id: UUID,
        parent_version_number: int,
        name: str,
        changes: List[FileChange]
    ) -> Optional[VersionResponse]:
        """Create a new version based on a parent version and apply changes.
        
        This is an alias for the create() method to maintain consistency with route naming.
        
        Args:
            project_id: Project UUID
            parent_version_number: Version number to base the new version on
            name: Name for the new version
            changes: List of file changes to apply
            
        Returns:
            New version with applied changes, or None if parent version not found
            
        Raises:
            ValueError: If file operations are invalid
        """
        return VersionCRUD.create(project_id, parent_version_number, name, changes)
        
    @staticmethod
    def create(
        project_id: UUID,
        parent_version_number: int,
        name: str,
        changes: List[FileChange]
    ) -> Optional[VersionResponse]:
        """Create a new version based on a parent version and apply changes.
        
        Args:
            project_id: Project UUID
            parent_version_number: Version number to base the new version on
            name: Name for the new version
            changes: List of file changes to apply
            
        Returns:
            New version with applied changes, or None if parent version not found
            
        Raises:
            ValueError: If file operations are invalid
        """
        client = get_supabase_client()
        
        # Get parent version
        parent_result = client.table("versions") \
            .select("*") \
            .eq("project_id", str(project_id)) \
            .eq("version_number", parent_version_number) \
            .execute()
            
        if not parent_result.data:
            return None
            
        parent_version = parent_result.data[0]
        
        # Get parent version files
        files_result = client.table("files") \
            .select("*") \
            .eq("version_id", parent_version["id"]) \
            .execute()
            
        # Create a map of existing files by path
        existing_files = {file["path"]: file for file in files_result.data}
        
        # TODO: Implement validate_file_changes and apply_file_changes as synchronous methods
        # For now, this code assumes these functions will be converted to sync
        # validate_file_changes(changes, existing_files)
        
        # Get next version number
        new_version_number = VersionCRUD.get_next_number(project_id)
        
        # Create new version
        version_data = {
            "project_id": str(project_id),
            "version_number": new_version_number,
            "parent_id": parent_version["id"],
            "name": name
        }
        
        # Insert new version
        new_version_result = client.table("versions").insert(version_data).execute()
        
        if not new_version_result.data:
            raise ValueError("Failed to create new version")
            
        new_version = new_version_result.data[0]
        
        # Apply file changes
        # For each file from parent version, create a copy or apply changes
        for path, file in existing_files.items():
            # Check if file is in changes
            file_change = next((c for c in changes if c.path == path), None)
            
            # If file is in changes and operation is DELETE, skip
            if file_change and file_change.operation == "DELETE":
                continue
                
            # If file is in changes and operation is UPDATE, use new content
            content = file_change.content if file_change and file_change.operation == "UPDATE" else file["content"]
            
            # Create file in new version
            file_data = {
                "version_id": new_version["id"],
                "path": path,
                "content": content
            }
            
            client.table("files").insert(file_data).execute()
        
        # Add any new files
        new_files = [c for c in changes if c.operation == "CREATE"]
        for file_change in new_files:
            file_data = {
                "version_id": new_version["id"],
                "path": file_change.path,
                "content": file_change.content
            }
            
            client.table("files").insert(file_data).execute()
        
        # Return the version response
        return VersionCRUD.get(project_id, new_version_number)
