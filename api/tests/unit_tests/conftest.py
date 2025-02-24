import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Load environment variables before importing app modules
env_path = Path(__file__).parent / "test.env"
load_dotenv(dotenv_path=env_path)

# Import app modules after environment is configured
from app.main import app
from app.config import get_db, settings

@pytest.fixture(scope="module")
def mock_db():
    """Mock database session for unit tests."""
    return MagicMock()

@pytest.fixture(scope="module")
def client(mock_db):
    """Test client with mocked database."""
    def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter service."""
    with patch('app.services.openrouter.OpenRouterService._get_client') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

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
        "parent_version_id": None
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
