import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.unit
def test_basic_mock():
    """Test that basic mocking works."""
    mock = MagicMock()
    mock.some_method.return_value = 42
    
    assert mock.some_method() == 42
    
@pytest.mark.unit
@pytest.mark.asyncio
async def test_basic_async_mock():
    """Test that async mocking works."""
    mock = AsyncMock()
    mock.some_async_method.return_value = 42
    
    result = await mock.some_async_method()
    assert result == 42
    assert mock.some_async_method.called

@pytest.mark.unit
def test_mock_db_session(mock_db):
    """Test that mock_db fixture works properly."""
    assert mock_db is not None
    assert hasattr(mock_db, 'commit')
    assert hasattr(mock_db, 'rollback')
    assert hasattr(mock_db, 'execute')