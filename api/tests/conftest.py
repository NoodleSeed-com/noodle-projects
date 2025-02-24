import os

# Set testing environment variable before importing any modules
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load test environment variables
load_dotenv("/Users/fahdrafi/VSCode/noodle-projects/api/tests/test.env")
os.environ["ENV_FILE"] = "tests/test.env"
print(f"DATABASE_URL from env: {os.environ.get('DATABASE_URL')}")

from app.main import app
from app.config import get_db, settings
from app.services.openrouter import get_openrouter
from app.models.base import Base

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine with proper pool configuration."""
    db_url = str(settings.DATABASE_URL).replace("+asyncpg", "")
    engine = create_engine(
        db_url,
        isolation_level="REPEATABLE READ",  # Ensure consistent reads
        pool_size=settings.POSTGRES_MAX_CONNECTIONS,  # Match max connections
        max_overflow=2,  # Allow some overflow for concurrent tests
        pool_timeout=30,  # Prevent indefinite waiting
        pool_pre_ping=True,  # Check connection validity
        echo=settings.DEBUG
    )
    # Create all tables once for the test session
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create an isolated test database session with transaction rollback.
    
    Each test gets its own connection and transaction, ensuring isolation
    between concurrent test runs.
    """
    # Create a new connection for this test
    connection = test_engine.connect()
    # Start a transaction
    transaction = connection.begin()
    # Create a session bound to this connection
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )
    db = TestingSessionLocal()
    
    # Create a savepoint for potential nested transactions
    db.begin_nested()
    
    yield db
    
    # Rollback everything
    db.rollback()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(test_db, mock_openrouter):
    """Create a test client with isolated database session.
    
    Function scope ensures each test gets a fresh client with its own
    database session, preventing interference between concurrent tests.
    """
    def override_get_db():
        return test_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_openrouter] = lambda: mock_openrouter
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_openrouter():
    """Mock OpenRouter service for testing.
    
    Uses MagicMock to track calls and provide better assertions
    for concurrent testing scenarios.
    """
    from unittest.mock import MagicMock
    from app.models.project import FileOperation, FileChange

    mock = MagicMock()
    # Default response for file changes
    mock.get_file_changes.return_value = [
        FileChange(
            operation=FileOperation.CREATE,
            path="src/test.tsx",
            content="export const Test = () => <div>Test</div>"
        )
    ]
    return mock

@pytest.fixture
def test_project():
    """Fixture for test project data."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing"
    }
