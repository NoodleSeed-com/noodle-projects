import os
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
from app.models.base import Base

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    db_url = str(settings.DATABASE_URL).replace("+asyncpg", "")
    engine = create_engine(db_url, echo=True)
    return engine

@pytest.fixture(scope="module")
def test_db(test_engine):
    """Create a test database session and tables."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="module")
def client(test_db):
    """Create a test client using the test database."""
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
        "description": "A test project for unit testing"
    }
