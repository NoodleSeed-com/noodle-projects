#!/usr/bin/env python
"""
Noodle Projects MCP server using the official MCP Python SDK.
"""
import asyncio
import sys
import json
from typing import Optional, Dict, Any, List
import requests
import os
from datetime import datetime, timezone
import uuid

from fastmcp import FastMCP
import mcp.types as types

# Supabase configuration from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://jsanjojgtyyfpnfqwhgx.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Create a FastMCP instance with debugging
print("Creating Noodle Projects MCP server...", file=sys.stderr)
app = FastMCP("NoodleProjects")

class SupabaseRESTClient:
    """Client for interacting with Supabase using the REST API."""
    
    def __init__(self):
        """Initialize the client with Supabase credentials."""
        self.url = SUPABASE_URL
        self.key = SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    async def list_projects(self, limit: int = 100, offset: int = 0, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """List all projects with pagination support."""
        # Build query filters
        active_filter = "" if include_inactive else "&active=eq.true"
        
        response = requests.get(
            f"{self.url}/rest/v1/projects?select=*&order=created_at.desc&limit={limit}&offset={offset}{active_filter}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID."""
        response = requests.get(
            f"{self.url}/rest/v1/projects?id=eq.{project_id}&select=*",
            headers=self.headers
        )
        response.raise_for_status()
        projects = response.json()
        return projects[0] if projects else None
    
    async def create_project(self, name: str, description: str) -> Dict[str, Any]:
        """Create a new project."""
        project_data = {
            "name": name,
            "description": description,
            "active": True
        }
        response = requests.post(
            f"{self.url}/rest/v1/projects",
            headers=self.headers,
            json=project_data
        )
        response.raise_for_status()
        created_project = response.json()
        
        # Handle both array and object responses
        if isinstance(created_project, list) and len(created_project) > 0:
            return created_project[0]
        elif isinstance(created_project, dict):
            return created_project
        else:
            # If we can't get data from response, query for the project we just created
            get_response = requests.get(
                f"{self.url}/rest/v1/projects?name=eq.{name}&order=created_at.desc&limit=1",
                headers=self.headers
            )
            get_response.raise_for_status()
            projects = get_response.json()
            if projects and len(projects) > 0:
                return projects[0]
            raise ValueError("Could not retrieve created project")

# Initialize the database client
client = SupabaseRESTClient()

# Define the tools

@app.tool(description="List all projects")
async def list_projects(limit: int = 100, offset: int = 0, include_inactive: bool = False) -> Dict[str, Any]:
    """List all projects with pagination support."""
    try:
        projects = await client.list_projects(limit=limit, offset=offset, include_inactive=include_inactive)
        return {
            "items": projects,
            "total": len(projects),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        print(f"Error listing projects: {str(e)}", file=sys.stderr)
        raise

@app.tool(description="Get project details by ID")
async def get_project(project_id: str) -> Dict[str, Any]:
    """Get a project by ID."""
    try:
        project = await client.get_project(project_id=project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        return project
    except Exception as e:
        print(f"Error getting project: {str(e)}", file=sys.stderr)
        raise

@app.tool(description="Create a new project")
async def create_project(name: str, description: str = "") -> Dict[str, Any]:
    """Create a new project."""
    try:
        project = await client.create_project(name=name, description=description)
        return project
    except Exception as e:
        print(f"Error creating project: {str(e)}", file=sys.stderr)
        raise

@app.tool(description="Check server health")
async def check_health() -> Dict[str, Any]:
    """Check the health of the MCP server and its backend services."""
    try:
        # Check database connectivity
        projects = await client.list_projects(limit=1)
        
        return {
            "status": "healthy",
            "database": "connected",
            "services": ["database", "openrouter"]
        }
    except Exception as e:
        print(f"Health check failed: {str(e)}", file=sys.stderr)
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Run the server directly if this file is executed
if __name__ == "__main__":
    print("Noodle Projects MCP server main entry point...", file=sys.stderr)
    app.run()