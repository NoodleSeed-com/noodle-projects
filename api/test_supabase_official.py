#!/usr/bin/env python
"""
Test script for the synchronous Supabase implementation using the official supabase-py client.
"""
import os
import uuid
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app.services.supabase.client import SupabaseService

def test_supabase_service():
    """Test the SupabaseService with basic CRUD operations."""
    print("Testing Supabase Service...")
    
    # Initialize service
    service = SupabaseService()
    
    # Health check
    health_response = service.check_health()
    print(f"Health check: {health_response['success']}")
    if not health_response["success"]:
        print(f"Error: {health_response.get('error', 'Unknown error')}")
        return False
        
    # Create a project
    project_name = f"Test Project {uuid.uuid4()}"
    print(f"Creating project: {project_name}")
    
    create_response = service.create_project(name=project_name, description="Test project from synchronous client")
    if not create_response["success"]:
        print(f"Error creating project: {create_response.get('error', 'Unknown error')}")
        return False
    
    project_id = create_response["data"]["id"]
    print(f"Project created with ID: {project_id}")
    
    # Get the project
    get_response = service.get_project(project_id=project_id)
    if not get_response["success"]:
        print(f"Error retrieving project: {get_response.get('error', 'Unknown error')}")
        return False
    
    project = get_response["data"]
    print(f"Retrieved project: {project['name']}")
    
    # Update the project
    updated_name = f"Updated Project {uuid.uuid4()}"
    print(f"Updating project to: {updated_name}")
    
    update_response = service.update_project(project_id=project_id, name=updated_name)
    if not update_response["success"]:
        print(f"Error updating project: {update_response.get('error', 'Unknown error')}")
        return False
    
    updated_project = update_response["data"]
    print(f"Project updated successfully: {updated_project['name']}")
    
    # Create a version 
    print("Creating version...")
    version_name = f"Version {uuid.uuid4()}"
    
    # First, we need to create the first version without a parent ID
    if True: # Simplified logic for initial tests
        print("Creating initial version with no parent...")
        # Directly add a version with the official Supabase client
        service_client = service.client
        version_id = str(uuid.uuid4())
        version_data = {
            "id": version_id,
            "project_id": project_id,
            "version_number": 1,
            "name": "Initial Version",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            response = service_client.table("versions").insert(version_data).execute()
            print(f"Initial version created with ID: {version_id}")
            
            # Now try to create a second version using the service
            version_response = service.create_version(
                project_id=project_id,
                name=version_name,
                parent_version_number=1  # Use the initial version we just created
            )
        except Exception as e:
            print(f"Error creating initial version: {e}")
            # Soft delete the project before exiting
            service.delete_project(project_id=project_id)
            return False
        
        if not version_response["success"]:
            print(f"Error creating version: {version_response.get('error', 'Unknown error')}")
            # Soft delete the project before exiting
            service.delete_project(project_id=project_id)
            return False
    
    version = version_response["data"]
    version_id = version["id"]
    print(f"Version created with ID: {version_id}")
    
    # File operations have been removed
    print("Skipping file operations (removed from API)")
    
    # Clean up - soft delete the project
    print(f"Soft deleting test project...")
    delete_response = service.delete_project(project_id=project_id)
    if not delete_response["success"]:
        print(f"Error deleting project: {delete_response.get('error', 'Unknown error')}")
        return False
    
    print("Project soft-deleted successfully")
    print("All tests passed!")
    return True

if __name__ == "__main__":
    success = test_supabase_service()
    sys.exit(0 if success else 1)