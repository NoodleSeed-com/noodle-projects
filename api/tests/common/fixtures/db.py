"""
Database fixtures for testing.
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any, Generator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings, get_engine, get_db

@pytest.fixture(scope="function")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for each test."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    # Ensure we're in test mode
    os.environ["TEST_MODE"] = "True"
    
    # Use SQLite for test database
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        test_db_url,
        echo=False,
        poolclass=NullPool
    )
    
    # Create tables
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        # Rollback any pending transactions
        await session.rollback()

@pytest.fixture(scope="function")
def mock_db_session() -> Dict[str, Any]:
    """Create a mock database session for unit tests."""
    # Return a dictionary of mock objects
    return {
        "db": MockDBSession(),
        "objects": {},
        "count": 0
    }

class MockDBSession:
    """Mock database session for unit tests."""
    
    def __init__(self):
        """Initialize the mock session."""
        self.objects = {}
        self.committed = False
        self.rolled_back = False
        self.closed = False
    
    async def commit(self):
        """Mock commit."""
        self.committed = True
    
    async def rollback(self):
        """Mock rollback."""
        self.rolled_back = True
    
    async def close(self):
        """Mock close."""
        self.closed = True
    
    async def refresh(self, obj):
        """Mock refresh."""
        # Do nothing
        pass
    
    async def execute(self, *args, **kwargs):
        """Mock execute."""
        return MockResult(self.objects)
    
    def add(self, obj):
        """Mock add."""
        # Store the object by its class name
        cls_name = obj.__class__.__name__
        if cls_name not in self.objects:
            self.objects[cls_name] = []
        self.objects[cls_name].append(obj)
    
    async def flush(self):
        """Mock flush."""
        # Do nothing
        pass

class MockResult:
    """Mock query result."""
    
    def __init__(self, objects):
        """Initialize the mock result."""
        self.objects = objects
    
    def scalar_one_or_none(self):
        """Mock scalar_one_or_none."""
        # Return the first object of any type
        for obj_list in self.objects.values():
            if obj_list:
                return obj_list[0]
        return None
    
    def scalars(self):
        """Mock scalars."""
        return self
    
    def unique(self):
        """Mock unique."""
        return self
    
    def all(self):
        """Mock all."""
        # Flatten all objects
        result = []
        for obj_list in self.objects.values():
            result.extend(obj_list)
        return result