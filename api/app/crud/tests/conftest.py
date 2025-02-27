"""Test fixtures for CRUD operations."""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from ...models.base import Base
from ...schemas.common import FileChange, FileOperation

@pytest.fixture
def event_loop():
    """Create a new event loop for each test.
    
    This prevents issues with loop closure and ensures each test
    gets a fresh event loop instance.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    
    # Mock the nested transaction context
    nested_transaction = AsyncMock()
    session.begin_nested.return_value.__aenter__.return_value = nested_transaction
    
    # Mock begin context
    session.begin.return_value.__aenter__.return_value = session
    
    # Track session state
    session.new = set()  # New objects pending commit
    session.deleted = set()  # Deleted objects pending commit
    session._relationships = {}  # Track relationships between objects
    session._data = {}  # Store mock data for queries
    
    # Mock common SQLAlchemy methods
    session.add = MagicMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.delete = MagicMock()
    session.get = MagicMock()
    session.flush = AsyncMock()
    
    # Create a custom mock class for query results
    class MockQueryResult:
        def __init__(self, scalar_value=None):
            self.scalar_value = scalar_value
            
        def scalar_one_or_none(self):
            return self.scalar_value
            
        def scalar_one(self):
            return True  # Default for active flag
            
        def unique(self):
            return self
            
        def all(self):
            return []
    
    # Use side_effect to return a MockQueryResult
    async def mock_execute(*args, **kwargs):
        return MockQueryResult()
        
    session.execute = AsyncMock(side_effect=mock_execute)
    
    # Mock commit to handle events and relationships
    async def mock_commit():
        # Run before_commit events
        for obj in session.new:
            if hasattr(obj, 'validate'):
                result = obj.validate(session)
                if hasattr(result, '__await__'):
                    await result
            
            # Set timestamps only if not already set
            if isinstance(obj, Base):
                now = datetime.now(timezone.utc)
                if not hasattr(obj, 'created_at') or obj.created_at is None:
                    obj.created_at = now
                if not hasattr(obj, 'updated_at') or obj.updated_at is None:
                    obj.updated_at = now
        
        # Handle cascade deletes
        deleted_objects = list(session.deleted)  # Create a copy to avoid modification during iteration
        for obj in deleted_objects:
            if isinstance(obj, Version):
                # Delete associated files
                files = session._relationships.get(obj.id, {}).get('files', [])
                for file in files:
                    session.deleted.add(file)
            
            # Remove from relationships
            if obj.id in session._relationships:
                del session._relationships[obj.id]
    
    session.commit = AsyncMock(side_effect=mock_commit)
    
    # Mock add to track new objects and relationships
    original_add = session.add
    def mock_add(obj):
        session.new.add(obj)
        
        # Track relationships
        if isinstance(obj, File) and obj.version_id:
            if obj.version_id not in session._relationships:
                session._relationships[obj.version_id] = {'files': []}
            session._relationships[obj.version_id]['files'].append(obj)
            
        return original_add(obj)
    session.add = MagicMock(side_effect=mock_add)
    
    # Mock delete to track deleted objects
    original_delete = session.delete
    def mock_delete(obj):
        session.deleted.add(obj)
        return original_delete(obj)
    session.delete = MagicMock(side_effect=mock_delete)
    
    yield session
    
    # Cleanup
    await session.close()

@pytest.fixture
def mock_project():
    """Create a mock project."""
    project = MagicMock(spec=Project)
    project.id = uuid4()
    project.name = "Test Project"
    project.description = "Test Description"
    project.active = True
    project.versions = []
    project.created_at = datetime.now(timezone.utc)
    project.updated_at = datetime.now(timezone.utc)
    return project

@pytest.fixture
def mock_version(mock_project):
    """Create a mock version."""
    version = MagicMock(spec=Version)
    version.id = uuid4()
    version.project_id = mock_project.id
    version.version_number = 0
    version.name = "Initial Version"
    version.parent_id = None
    version.files = []
    version.created_at = datetime.now(timezone.utc)
    version.updated_at = datetime.now(timezone.utc)
    mock_project.versions.append(version)
    return version

@pytest.fixture
def mock_files(mock_version):
    """Create mock files for a version."""
    files = []
    file_paths = [
        "package.json",
        "tsconfig.json",
        "public/index.html",
        "src/App.tsx",
        "src/index.tsx",
        "src/components/HelloWorld.tsx"
    ]
    
    for path in file_paths:
        file = MagicMock(spec=File)
        file.id = uuid4()
        file.version_id = mock_version.id
        file.path = path
        file.content = f"Content for {path}"
        file.created_at = datetime.now(timezone.utc)
        file.updated_at = datetime.now(timezone.utc)
        files.append(file)
        mock_version.files.append(file)
    
    return files

@pytest.fixture
def file_changes():
    """Create sample file changes."""
    return [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/components/NewComponent.tsx",
            content="export const NewComponent = () => <div>New Component</div>;"
        ),
        FileChange(
            operation=FileOperation.UPDATE,
            path="src/App.tsx",
            content="import React from 'react';\n\nexport const App = () => <div>Updated App</div>;"
        ),
        FileChange(
            operation=FileOperation.DELETE,
            path="src/components/HelloWorld.tsx"
        )
    ]
