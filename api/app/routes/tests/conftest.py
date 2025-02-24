"""Test fixtures for routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from ...main import app
from ...services.openrouter import get_openrouter

@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter service for testing."""
    async def mock_service():
        mock = MagicMock()
        mock.get_file_changes.return_value = []
        return mock
    
    app.dependency_overrides[get_openrouter] = mock_service
    yield mock_service
    app.dependency_overrides.clear()

@pytest.fixture
def client(mock_db: Session):
    """Test client with mocked database."""
    with TestClient(app) as client:
        yield client
