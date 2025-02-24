"""Test fixtures for models."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

@pytest_asyncio.fixture(scope="function")
async def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    
    # Mock the nested transaction context
    nested_transaction = AsyncMock()
    session.begin_nested.return_value.__aenter__.return_value = nested_transaction
    
    # Mock common SQLAlchemy methods
    session.add = MagicMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.query = MagicMock()
    session.get = MagicMock()
    session.new = set()  # Track new objects for event handling
    
    # Mock commit to handle events
    async def mock_commit():
        # Run before_commit events
        for obj in session.new:
            if hasattr(obj, 'validate'):
                result = obj.validate(session)
                # Handle both async and sync validate methods
                if hasattr(result, '__await__'):
                    await result
    
    session.commit = AsyncMock(side_effect=mock_commit)
    
    # Mock add to track new objects
    original_add = session.add
    def mock_add(obj):
        session.new.add(obj)
        return original_add(obj)
    session.add = MagicMock(side_effect=mock_add)
    
    yield session
    
    # Ensure all mocked methods were called as expected
    await session.close()

@pytest.fixture
def mock_models():
    """Create mock models for testing."""
    models = MagicMock()
    models.Project = MagicMock()
    models.Version = MagicMock()
    models.File = MagicMock()
    return models
