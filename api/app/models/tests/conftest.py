"""Test fixtures for models."""
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
from ...models.base import BaseSchema

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
    
    # Track session state
    session.new = set()  # New objects pending commit
    session.deleted = set()  # Deleted objects pending commit
    session._relationships = {}  # Track relationships between objects
    
    # Mock common SQLAlchemy methods
    session.add = MagicMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.delete = MagicMock()
    session.get = MagicMock()
    
    # Mock query builder
    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.all.return_value = []
    session.query = MagicMock(return_value=query_mock)
    
    # Mock commit to handle events and relationships
    async def mock_commit():
        # Run before_commit events
        for obj in session.new:
            if hasattr(obj, 'validate'):
                result = obj.validate(session)
                if hasattr(result, '__await__'):
                    await result
            
            # Set timestamps only if not already set
            if isinstance(obj, BaseSchema):
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
def mock_models():
    """Create mock models for testing."""
    models = MagicMock()
    
    # Setup Project mock
    project_mock = MagicMock(spec=Project)
    project_mock.id = uuid4()
    project_mock.active = True
    project_mock.versions = []
    models.Project = MagicMock(return_value=project_mock)
    
    # Setup Version mock
    version_mock = MagicMock(spec=Version)
    version_mock.id = uuid4()
    version_mock.files = []
    type(version_mock).active = PropertyMock(return_value=True)
    models.Version = MagicMock(return_value=version_mock)
    
    # Setup File mock
    file_mock = MagicMock(spec=File)
    file_mock.id = uuid4()
    models.File = MagicMock(return_value=file_mock)
    
    # Add TestModel support
    test_model_mock = MagicMock(spec=BaseSchema)
    # Let the test set these values
    test_model_mock.id = None
    test_model_mock.created_at = None
    test_model_mock.updated_at = None
    models.TestModel = MagicMock(return_value=test_model_mock)
    
    return models
