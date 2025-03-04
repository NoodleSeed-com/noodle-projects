"""Template handling for initial version creation using Supabase."""
import os
from uuid import UUID
from typing import Dict, Any

from ...config import settings
from ...services.supabase.client import get_supabase_client

def create_initial_version(project_id: UUID) -> Dict[str, Any]:
    """Create version 0 with template files for a new project."""
    client = get_supabase_client()
    
    # Create version
    version_data = {
        "project_id": str(project_id),
        "version_number": 0,
        "name": "Initial Version"
    }
    
    # Insert version
    version_result = client.table("versions").insert(version_data).execute()
    
    if not version_result.data:
        raise ValueError("Failed to create initial version")
        
    version = version_result.data[0]
    
    # Read and add template files from settings.TEMPLATE_PATH
    template_dir = os.path.join(settings.TEMPLATE_PATH, 'version-0')
    
    # Collect all files first
    file_paths = []
    for root, _, files in os.walk(template_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, template_dir)
            file_paths.append((file_path, relative_path))
    
    # Process files sequentially
    for file_path, relative_path in file_paths:
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Create file data
        file_data = {
            "version_id": version["id"],
            "path": relative_path,
            "content": content
        }
        
        # Insert file
        client.table("files").insert(file_data).execute()
    
    # Return the created version
    return version
