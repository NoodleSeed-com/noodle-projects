"""File operations for version management."""
from typing import Dict, List
from uuid import UUID

from ...models.file import File
from ...schemas.common import FileOperation, FileChange

async def validate_file_changes(changes: List[FileChange], existing_files: Dict[str, File]) -> None:
    """Validate file changes before applying them.
    
    Args:
        changes: List of file changes to validate
        existing_files: Dictionary of existing files by path
        
    Raises:
        ValueError: If validation fails
    """
    paths = {}
    for change in changes:
        if not change.path or not change.path.strip():
            raise ValueError("File path cannot be empty")
            
        if change.operation in (FileOperation.CREATE, FileOperation.UPDATE) and not change.content:
            raise ValueError(f"Content required for {change.operation} operation on {change.path}")
        
        # Check for duplicate paths in changes
        if change.path in paths:
            raise ValueError(f"Duplicate file path in changes: {change.path}")
        paths[change.path] = True
        
        # Validate operation-specific rules
        if change.operation == FileOperation.CREATE and change.path in existing_files:
            raise ValueError(f"Cannot create file that already exists: {change.path}")
        elif change.operation in (FileOperation.UPDATE, FileOperation.DELETE):
            if change.path not in existing_files:
                raise ValueError(f"Cannot {change.operation.value} non-existent file: {change.path}")

async def apply_file_changes(
    new_version_id: UUID,
    changes: List[FileChange],
    existing_files: Dict[str, File]
) -> List[File]:
    """Apply file changes to create new version files.
    
    Args:
        new_version_id: UUID of the new version
        changes: List of file changes to apply
        existing_files: Dictionary of existing files by path
        
    Returns:
        List of File objects for the new version
    """
    # Start with copies of all existing files
    files_to_add = [
        File(
            version_id=new_version_id,
            path=path,
            content=file.content
        )
        for path, file in existing_files.items()
    ]
    
    # Apply changes
    for change in changes:
        if change.operation == FileOperation.CREATE:
            files_to_add.append(File(
                version_id=new_version_id,
                path=change.path,
                content=change.content
            ))
        elif change.operation == FileOperation.UPDATE:
            # Remove old file and add updated one
            files_to_add = [f for f in files_to_add if f.path != change.path]
            files_to_add.append(File(
                version_id=new_version_id,
                path=change.path,
                content=change.content
            ))
        elif change.operation == FileOperation.DELETE:
            # Remove file from list
            files_to_add = [f for f in files_to_add if f.path != change.path]
    
    return files_to_add
