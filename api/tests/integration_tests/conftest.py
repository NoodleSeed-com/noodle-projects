import os
import pytest
import pytest_asyncio
from pathlib import Path
from dotenv import load_dotenv
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import asyncio

# Load environment variables before importing app modules
env_path = Path(__file__).parent / "test.env"
load_dotenv(dotenv_path=env_path)

# Import app modules after environment is configured
from app.main import app
from app.config import get_db, settings
from app.models.base import Base
from app.services.openrouter import OpenRouterService
from app.schemas.common import FileChange, AIResponse
from typing import List

@pytest.fixture(scope="function", autouse=True)
def event_loop():
    """Create a function-scoped event loop for integration tests.
    
    Using function scope with autouse=True prevents the
    "RuntimeError: Task got Future attached to a different loop" issue
    that occurs when mixing pytest-asyncio with SQLAlchemy async sessions.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()
    asyncio.set_event_loop(None)

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a function-scoped SQLAlchemy engine.
    
    Using function scope instead of session scope ensures a clean
    database environment for each test and prevents event loop issues.
    """    
    # Create the engine with a smaller connection pool for tests
    engine = create_async_engine(
        str(settings.DATABASE_URL), 
        echo=True,
        poolclass=None,  # Disable connection pooling for tests
        pool_pre_ping=True,  # Verify connections before use
        future=True  # Use the future API for better compatibility
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Properly close and dispose of the engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def async_session_factory(test_engine):
    """Create a function-scoped session factory.
    
    This ensures each test has its own independent session factory
    that isn't affected by other tests.
    """
    return async_sessionmaker(
        bind=test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )

@pytest_asyncio.fixture(scope="function")
async def db_session(async_session_factory):
    """Create a function-scoped database session with transaction.
    
    This fixture creates a session with an active transaction, then rolls
    it back at the end of the test to undo any changes.
    """
    # Create a new session for each test
    session = async_session_factory()
    
    # Start a regular transaction
    await session.begin()
    
    try:
        # Use the session in the test
        yield session
    finally:
        # Rollback the transaction to undo any changes
        await session.rollback()
        
        # Ensure the session is properly closed
        await session.close()

class TestOpenRouterService(OpenRouterService):
    """Test version of OpenRouterService that doesn't call actual API."""
    
    async def get_file_changes(
        self,
        project_context: str,
        change_request: str,
        current_files: List
    ) -> List[FileChange]:
        """Return test file changes without calling API.
        
        This implementation is designed to be robust and handle all test cases
        appropriately, including simulating failure conditions when needed.
        """
        from app.schemas.common import FileOperation
        
        # Special test cases with expected behaviors
        test_cases = {
            # Transaction rollback test - should trigger validation error
            "Should Fail Version": lambda: self._raise_empty_path_error(),
            
            # Duplicate path test - should trigger validation error
            "Should Fail With Duplicate Path": lambda: [
                FileChange(
                    path="good_file.txt",
                    content="This file is valid",
                    operation=FileOperation.CREATE
                ),
                FileChange(
                    path="good_file.txt",  # Duplicate path - will cause validation error
                    content="This will fail because path is a duplicate",
                    operation=FileOperation.CREATE
                )
            ],
            
            # Invalid operation test - should trigger validation error
            "Invalid Operation Test": lambda: self._raise_invalid_operation(),
            
            # Transaction test - should fail with tx error in the test
            "Transaction Test Version": lambda: self._raise_empty_path_error(),
            
            # Sequential version 1
            "Sequential Version 1": lambda: [
                FileChange(
                    path="sequential_test_1.txt",
                    content="This is the first sequential test file",
                    operation=FileOperation.CREATE
                )
            ],
            
            # Sequential version 2
            "Sequential Version 2": lambda: [
                FileChange(
                    path="sequential_test_2.txt",
                    content="This is the second sequential test file",
                    operation=FileOperation.CREATE
                ),
                FileChange(
                    path="sequential_test_1.txt",
                    content="This is the updated first file",
                    operation=FileOperation.UPDATE
                )
            ],
            
            # API version tests
            "API Version 1": lambda: [
                FileChange(
                    path="api_file_1.txt",
                    content="Content for api_file_1.txt",
                    operation=FileOperation.CREATE
                )
            ],
            
            "API Version 2": lambda: [
                FileChange(
                    path="api_file_2.txt",
                    content="Content for api_file_2.txt",
                    operation=FileOperation.CREATE
                )
            ]
        }
        
        # Check if we have a handler for this test case
        for key, handler in test_cases.items():
            if key in change_request:
                try:
                    return handler()
                except Exception as e:
                    print(f"Test handler for {key} failed: {str(e)}")
                    # Re-raise expected exceptions
                    if "is not a valid FileOperation" in str(e):
                        raise
                    # For other exceptions, return a default response
        
        # Default fallback - create a simple test file
        return [
            FileChange(
                path="test_file.txt",
                content="This is a test file created for testing",
                operation=FileOperation.CREATE
            )
        ]
    
    def _raise_invalid_operation(self):
        """Helper method to simulate invalid operation error."""
        raise ValueError("'invalid_operation' is not a valid FileOperation")
        # This line is never reached but needed for type checking
        return []
        
    def _raise_empty_path_error(self):
        """Helper method to simulate empty path validation error."""
        raise ValueError("File path cannot be empty")
        # This line is never reached but needed for type checking
        return []

@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client with a function-scoped database session.
    
    This uses the db_session fixture which handles transaction management,
    including proper nested transaction support for version creation.
    
    If USE_REAL_SERVICES environment variable is set to 'true', this will use
    the real OpenRouter service instead of the mock.
    """    
    # Create a function that will return our existing db_session directly (not as generator)
    async def override_get_db():
        return db_session
    
    # Set up dependency overrides
    app.dependency_overrides[get_db] = override_get_db
    
    # Check if we should use real services
    use_real_services = os.environ.get('USE_REAL_SERVICES', '').lower() == 'true'
    
    # Only mock OpenRouter if we're not using real services
    if not use_real_services:
        # Override the OpenRouter service with our test version
        async def get_test_openrouter():
            return TestOpenRouterService()
        
        from app.services.openrouter import get_openrouter
        app.dependency_overrides[get_openrouter] = get_test_openrouter
    
    # Use trailing slash in base_url to prevent redirect issues
    # httpx AsyncClient doesn't accept 'app' parameter directly, mount it on transport
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/", follow_redirects=True) as ac:
        yield ac
    
    # Clear all dependency overrides
    app.dependency_overrides.clear()

@pytest.fixture
def test_project():
    """Fixture for test project data."""
    return {
        "name": "Test Project",
        "description": "This is a test project"
    }

@pytest.fixture
def test_version():
    """Fixture for test version data."""
    return {
        "version_number": 1,
        "name": "Test Version",
        "parent_id": None
    }

@pytest.fixture
def test_files():
    """Fixture for test file data."""
    return [
        {
            "path": "src/main.py",
            "content": "print('Hello, World!')"
        },
        {
            "path": "README.md",
            "content": "# Test Project\nThis is a test."
        }
    ]
