"""Test fixtures for models."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from ...models.base import Base
from ...config import get_db, settings

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    db_url = str(settings.DATABASE_URL).replace("+asyncpg", "")  # Make sure it is sync
    engine = create_engine(db_url, echo=True)
    return engine

@pytest.fixture(scope="module")
def test_db(test_engine):
    """Create test database session."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_db: Session):
    """Provide database session that rolls back after each test."""
    test_db.begin_nested()  # Create savepoint
    yield test_db
    test_db.rollback()  # Rollback to savepoint
    test_db.expire_all()
