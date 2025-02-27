"""Tests for file CRUD operations."""
import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy import select
from ...models.file import File
from ...schemas.file import FileResponse
from ..file import FileCRUD

@pytest.mark.asyncio
async def test_get_by_version(mock_db_session, mock_files, mock_version):
    """Test getting all files for a specific version."""
    # Setup: Configure mock session to return our mock files
    async def mock_execute(*args, **kwargs):
        query = args[0]
        # Check if the query is for files by version
        if hasattr(query, '_where_criteria') and len(query._where_criteria) > 0:
            criteria = query._where_criteria[0]
            if hasattr(criteria, 'left') and hasattr(criteria.left, 'key') and criteria.left.key == 'version_id':
                version_id = criteria.right.value
                if version_id == mock_version.id:
                    class MockScalars:
                        def all(self):
                            return mock_files
                    
                    class MockResult:
                        def scalars(self):
                            return MockScalars()
                    
                    return MockResult()
        
        # Default empty result
        class MockDefault:
            def scalars(self):
                class Empty:
                    def all(self):
                        return []
                return Empty()
        
        return MockDefault()
    
    mock_db_session.execute.side_effect = mock_execute
    
    # Execute
    files = await FileCRUD.get_by_version(mock_db_session, mock_version.id)
    
    # Assert
    assert len(files) == len(mock_files)
    for i, file in enumerate(files):
        assert isinstance(file, FileResponse)
        assert file.id == mock_files[i].id
        assert file.path == mock_files[i].path
        assert file.content == mock_files[i].content

@pytest.mark.asyncio
async def test_get_by_version_empty(mock_db_session):
    """Test getting files for a version with no files."""
    # Setup: Configure mock to return empty list
    async def mock_execute(*args, **kwargs):
        class MockScalars:
            def all(self):
                return []
        
        class MockResult:
            def scalars(self):
                return MockScalars()
        
        return MockResult()
    
    mock_db_session.execute.side_effect = mock_execute
    
    # Execute
    files = await FileCRUD.get_by_version(mock_db_session, uuid4())
    
    # Assert
    assert len(files) == 0
    assert isinstance(files, list)

@pytest.mark.asyncio
async def test_get_by_path_found(mock_db_session, mock_files, mock_version):
    """Test getting a specific file by path when it exists."""
    # Choose a mock file to test with
    mock_file = mock_files[0]
    file_path = mock_file.path
    
    # Setup: Configure mock to return our specific file
    async def mock_execute(*args, **kwargs):
        query = args[0]
        # Check if the query is for a specific file path within a version
        if hasattr(query, '_where_criteria') and len(query._where_criteria) >= 2:
            version_match = False
            path_match = False
            
            for criteria in query._where_criteria:
                if hasattr(criteria, 'left') and hasattr(criteria.left, 'key'):
                    if criteria.left.key == 'version_id' and criteria.right.value == mock_version.id:
                        version_match = True
                    if criteria.left.key == 'path' and criteria.right.value == file_path:
                        path_match = True
            
            if version_match and path_match:
                class MockResult:
                    def scalar_one_or_none(self):
                        return mock_file
                
                return MockResult()
        
        # Default no result
        class MockDefault:
            def scalar_one_or_none(self):
                return None
        
        return MockDefault()
    
    mock_db_session.execute.side_effect = mock_execute
    
    # Execute
    file_response = await FileCRUD.get_by_path(mock_db_session, mock_version.id, file_path)
    
    # Assert
    assert file_response is not None
    assert isinstance(file_response, FileResponse)
    assert file_response.id == mock_file.id
    assert file_response.path == mock_file.path
    assert file_response.content == mock_file.content

@pytest.mark.asyncio
async def test_get_by_path_not_found(mock_db_session, mock_version):
    """Test getting a file by path when it doesn't exist."""
    # Setup: Configure mock to return None (file not found)
    async def mock_execute(*args, **kwargs):
        class MockResult:
            def scalar_one_or_none(self):
                return None
        
        return MockResult()
    
    mock_db_session.execute.side_effect = mock_execute
    
    # Execute
    file_response = await FileCRUD.get_by_path(mock_db_session, mock_version.id, "nonexistent/path.txt")
    
    # Assert
    assert file_response is None