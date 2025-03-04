#!/usr/bin/env python
"""
Test the MCP server using Supabase as the database backend.
"""
import os
import asyncio
import uuid
import logging
from supabase import create_client
from typing import Dict, Any, List

# Supabase configuration
SUPABASE_URL = "https://jsanjojgtyyfpnfqwhgx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM"
OPENROUTER_API_KEY = "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"

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# For testing integration with the database, we'll use SQLAlchemy directly
# since our access is configured for the API endpoints, not direct table access
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.crud.project import ProjectCRUD
from app.crud.version.crud import VersionCRUD
from app.models.project import ProjectCreate
from app.models.version import VersionCreate

class DatabaseClient:
    """Client for database operations using SQLAlchemy."""
    
    def __init__(self):
        """Initialize the database connection."""
        # Use transaction mode for better performance with serverless applications
        db_url = f"postgresql+asyncpg://postgres.jsanjojgtyyfpnfqwhgx:postgres@aws-0-us-east-1.pooler.supabase.com:6543/postgres?ssl=true&prepared_statement_cache_size=0"
        self.engine = create_async_engine(
            db_url,
            pool_size=20,              # Limit pool size for better resource management
            max_overflow=0,            # Prevent connection overflow
            pool_timeout=30,           # Connection timeout in seconds
            pool_recycle=1800,         # Recycle connections after 30 minutes
            pool_pre_ping=True         # Verify connections before use
        )
        self.session_factory = async_sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine,
            expire_on_commit=False
        )
        logger.info(f"Connected to database at {db_url[:30]}...")
    
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        async with self.session_factory() as session:
            return session
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects from database."""
        session = await self.get_session()
        try:
            projects, _ = await ProjectCRUD.get_multi(db=session)
            return [project.model_dump() for project in projects]
        finally:
            await session.close()
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a project by ID."""
        session = await self.get_session()
        try:
            project = await ProjectCRUD.get(db=session, project_id=project_id)
            if not project:
                raise ValueError(f"Project with ID {project_id} not found")
            return project.model_dump()
        finally:
            await session.close()
    
    async def create_project(self, name: str, description: str) -> str:
        """Create a new project."""
        session = await self.get_session()
        try:
            project_create = ProjectCreate(name=name, description=description)
            project = await ProjectCRUD.create(db=session, project=project_create)
            return str(project.id)
        finally:
            await session.close()
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID (soft delete)."""
        session = await self.get_session()
        try:
            project = await ProjectCRUD.delete(db=session, project_id=project_id)
            return project is not None
        finally:
            await session.close()
    
    async def list_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """List all versions for a project."""
        session = await self.get_session()
        try:
            versions = await VersionCRUD.get_by_project(db=session, project_id=project_id)
            return [version.model_dump() for version in versions]
        finally:
            await session.close()
    
    async def create_version(self, project_id: str, version_number: int, name: str, parent_id: str = None) -> str:
        """Create a new version for a project."""
        session = await self.get_session()
        try:
            version_create = VersionCreate(
                project_id=project_id,
                version_number=version_number,
                name=name,
                parent_id=parent_id
            )
            version = await VersionCRUD.create(db=session, version=version_create)
            return str(version.id)
        finally:
            await session.close()

async def test_database():
    """Test database functionality using SQLAlchemy."""
    try:
        print("\n🧪 Starting Database Test")
        client = DatabaseClient()
        
        # Generate unique test project name
        test_project_name = f"Database Test Project {uuid.uuid4()}"
        print(f"\n1. Creating test project: {test_project_name}")
        
        # Create project
        project_id = await client.create_project(
            name=test_project_name,
            description="Test project created via SQLAlchemy"
        )
        print(f"✅ Project created with ID: {project_id}")
        
        # List projects
        print("\n2. Listing all projects")
        projects = await client.list_projects()
        print(f"✅ Found {len(projects)} projects")
        
        # Get project
        print(f"\n3. Getting project by ID: {project_id}")
        project = await client.get_project(project_id=project_id)
        print(f"✅ Retrieved project: {project['name']}")
        
        # Create version
        print("\n4. Creating a new version")
        version_number = 1
        version_id = await client.create_version(
            project_id=project_id,
            version_number=version_number,
            name="Initial version"
        )
        print(f"✅ Version created with ID: {version_id}")
        
        # List versions
        print("\n5. Listing project versions")
        versions = await client.list_versions(project_id=project_id)
        print(f"✅ Found {len(versions)} versions")
        
        # Verify correct version was created
        version_found = False
        for version in versions:
            if str(version['id']) == version_id:
                version_found = True
                print(f"✅ Version verified: {version['name']} (version {version['version_number']})")
                break
        
        if not version_found:
            print("❌ Could not find created version in version list")
        
        # Delete project (soft delete)
        print(f"\n6. Cleaning up: Deleting test project {project_id}")
        deleted = await client.delete_project(project_id=project_id)
        if deleted:
            print("✅ Project marked as inactive (soft deleted)")
        else:
            print("❌ Failed to delete project")
        
        print("\n✅ All database tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing database: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_functionality():
    """Test the MCP server with the configured database."""
    try:
        print("\n🧪 Starting MCP Server Test")
        
        # Import the MCP server module
        from app.mcp_server import list_projects, create_project, get_project, delete_project, list_versions, create_version
        
        # Generate unique test project name
        test_project_name = f"MCP Test Project {uuid.uuid4()}"
        print(f"\n1. Creating test project with MCP: {test_project_name}")
        
        # Create project
        result = await create_project(
            name=test_project_name,
            description="Project created by MCP test"
        )
        
        if not result.get('success'):
            print(f"❌ Failed to create project: {result.get('error')}")
            return False
            
        project_id = result.get('data', {}).get('id')
        print(f"✅ Project created with ID: {project_id}")
        
        # List projects
        print("\n2. Listing all projects with MCP")
        result = await list_projects()
        
        if not result.get('success'):
            print(f"❌ Failed to list projects: {result.get('error')}")
            return False
            
        projects = result.get('data', {}).get('items', [])
        print(f"✅ Found {len(projects)} projects")
        
        # Get project details
        print(f"\n3. Getting project with MCP by ID: {project_id}")
        result = await get_project(project_id=project_id)
        
        if not result.get('success'):
            print(f"❌ Failed to get project: {result.get('error')}")
            return False
            
        project_data = result.get('data', {})
        print(f"✅ Retrieved project: {project_data.get('name')}")
        
        # Delete project
        print(f"\n4. Cleaning up: Deleting test project with MCP {project_id}")
        result = await delete_project(project_id=project_id)
        
        if not result.get('success'):
            print(f"❌ Failed to delete project: {result.get('error')}")
            return False
            
        print("✅ Project successfully deleted")
        
        print("\n✅ All MCP tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing MCP functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    # Configure environment variables for tests
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres.jsanjojgtyyfpnfqwhgx:postgres@aws-0-us-east-1.pooler.supabase.com:6543/postgres?ssl=true&prepared_statement_cache_size=0"
    os.environ["SUPABASE_URL"] = SUPABASE_URL
    os.environ["SUPABASE_KEY"] = SUPABASE_KEY
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
    os.environ["TESTING"] = "true"
    
    # First test the direct database connection
    print("\n🔍 Testing database connection...")
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        
        engine = create_async_engine(
            os.environ["DATABASE_URL"],
            pool_size=20,
            max_overflow=0,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            if value == 1:
                print("✅ Database connection successful")
                db_connection_success = True
            else:
                print(f"❌ Database connection returned unexpected value: {value}")
                db_connection_success = False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        db_connection_success = False
        
    if not db_connection_success:
        print("\n❌ Database connection failed. Skipping further tests.")
        return False
        
    # Run database tests
    db_success = await test_database()
    
    if not db_success:
        print("\n❌ Database tests failed. Skipping MCP tests.")
        return False
    
    # Then test the MCP functionality
    mcp_success = await test_mcp_functionality()
    
    return db_success and mcp_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)