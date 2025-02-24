import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables before importing app modules
env_path = Path(__file__).parent / "test.env"
load_dotenv(dotenv_path=env_path)

# Import app modules after environment is configured
from app.main import app
from app.config import get_db, settings
from app.models.base import Base

@pytest.fixture(scope="session")
def test_engine():
    db_url = str(settings.DATABASE_URL).replace("+asyncpg", "")  # Make sure it is sync
    engine = create_engine(db_url, echo=True)
    return engine

@pytest.fixture(scope="module")
def test_db(test_engine):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        return test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
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
