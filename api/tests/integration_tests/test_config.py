"""
Tests for configuration module.
"""
import pytest
from sqlalchemy.exc import SQLAlchemyError
from app.config import Settings, get_db

def test_settings_debug_mode():
    """Test debug mode configuration."""
    settings = Settings(DEBUG=True, DATABASE_URL="postgresql://user:pass@localhost/db")
    assert settings.DEBUG is True
    
    settings = Settings(DEBUG=False, DATABASE_URL="postgresql://user:pass@localhost/db")
    assert settings.DEBUG is False

def test_settings_cors_origins():
    """Test CORS origins configuration."""
    settings = Settings(
        BACKEND_CORS_ORIGINS=["http://localhost", "https://example.com"],
        DATABASE_URL="postgresql://user:pass@localhost/db"
    )
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
    assert "http://localhost" in settings.BACKEND_CORS_ORIGINS
    assert "https://example.com" in settings.BACKEND_CORS_ORIGINS

def test_database_url_formats():
    """Test different database URL formats."""
    # Test standard format
    settings = Settings(DATABASE_URL="postgresql://user:pass@localhost/db")
    assert str(settings.DATABASE_URL).startswith("postgresql://")
    
    # Test asyncpg format
    settings = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db")
    assert "postgresql+asyncpg" in str(settings.DATABASE_URL)

async def test_get_db_error_handling(monkeypatch):
    """Test database session error handling."""
    class MockSession:
        def __init__(self):
            self.closed = False
        
        def close(self):
            self.closed = True
    
    session = MockSession()
    
    def mock_session():
        return session
    
    monkeypatch.setattr("app.config.SessionLocal", mock_session)
    
    # Test normal operation
    db_gen = get_db()
    db = await anext(db_gen)
    assert isinstance(db, MockSession)
    assert not session.closed  # Session should not be closed yet
    
    # Simulate generator completion
    try:
        next(db_gen)
    except StopIteration:
        pass
    
    assert session.closed  # Session should be closed after generator completes
    
    # Test error handling
    session.closed = False  # Reset for error test
    db_gen = get_db()
    db = await anext(db_gen)
    
    # Simulate error
    try:
        await db_gen.athrow(SQLAlchemyError("Test error"))
    except SQLAlchemyError:
        pass
    
    assert session.closed  # Session should be closed after error
