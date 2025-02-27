"""Test SQLAlchemy event listeners."""
import os
import pytest
from unittest.mock import patch, mock_open
from uuid import uuid4

from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from ...crud.version.template import create_initial_version

@pytest.mark.asyncio
async def test_create_initial_version(mock_db_session):
    """Test initial version creation after project insert."""
    # Create a project with mock session
    project = Project(id=uuid4(), name="Test Project")
    project._sa_session = mock_db_session
    mock_db_session.add(project)
    
    # Mock template files with proper dictionary syntax
    mock_files = {
        'package.json': '{"name": "test"}',
        'src/App.tsx': 'export default App',
        'src/index.tsx': 'import App from "./App"'
    }
    
    # Setup mock file structure and content
    with patch('os.path.dirname') as mock_dirname, \
         patch('os.path.join') as mock_join, \
         patch('os.walk') as mock_walk, \
         patch('os.path.relpath') as mock_relpath, \
         patch('builtins.open', create=True) as mock_file_open:
        
        # Mock dirname to return a fixed path
        mock_dirname.return_value = '/mock/path'
        
        # Mock join to return predictable paths
        def mock_join_impl(*args):
            return '/'.join(args)
        mock_join.side_effect = mock_join_impl
        
        # Setup mock file structure
        mock_walk.return_value = [
            ('/mock/path/templates/version-0', [], ['package.json']),
            ('/mock/path/templates/version-0/src', [], ['App.tsx', 'index.tsx'])
        ]
        
        # Mock relpath to return the expected relative paths
        def mock_relpath_impl(path, start):
            if 'package.json' in path:
                return 'package.json'
            elif 'App.tsx' in path:
                return 'src/App.tsx'
            elif 'index.tsx' in path:
                return 'src/index.tsx'
        mock_relpath.side_effect = mock_relpath_impl
        
        # Setup mock file reads
        mock_file_open.side_effect = [
            mock_open(read_data=content).return_value
            for content in mock_files.values()
        ]
        
        # Trigger event
        await create_initial_version(None, None, project)
        
        # Get created version
        versions = [obj for obj in mock_db_session.new if isinstance(obj, Version)]
        assert len(versions) == 1
        version = versions[0]
        
        # Verify version creation
        assert version.project_id == project.id
        assert version.version_number == 0
        assert version.name == "Initial Version"
        
        # Verify file creation
        files = [obj for obj in mock_db_session.new if isinstance(obj, File)]
        assert len(files) == len(mock_files)
        
        # Verify each file's content and path
        file_paths = {file.path: file.content for file in files}
        assert file_paths == mock_files
        
        # Verify session operations
        assert mock_db_session.commit.await_count == 2  # One for version, one for files
        assert mock_db_session.refresh.await_count == 1  # For version after first commit

@pytest.mark.asyncio
async def test_create_initial_version_no_session(mock_db_session):
    """Test handling when no session is available."""
    project = Project(id=uuid4(), name="Test Project")
    # Don't add to session to test no-session case
    
    # Call event directly
    await create_initial_version(None, None, project)
    
    # Verify no operations occurred
    assert len(mock_db_session.new) == 0
    assert mock_db_session.commit.await_count == 0
    assert mock_db_session.refresh.await_count == 0

@pytest.mark.asyncio
async def test_create_initial_version_file_error(mock_db_session):
    """Test handling of file read errors."""
    # Create a project with mock session
    project = Project(id=uuid4(), name="Test Project")
    project._sa_session = mock_db_session
    mock_db_session.add(project)
    
    with patch('os.path.dirname') as mock_dirname, \
         patch('os.path.join') as mock_join, \
         patch('os.walk') as mock_walk, \
         patch('os.path.relpath') as mock_relpath, \
         patch('builtins.open', create=True) as mock_file_open:
        
        # Mock dirname to return a fixed path
        mock_dirname.return_value = '/mock/path'
        
        # Mock join to return predictable paths
        def mock_join_impl(*args):
            return '/'.join(args)
        mock_join.side_effect = mock_join_impl
        
        # Setup mock file structure
        mock_walk.return_value = [
            ('/mock/path/templates/version-0', [], ['package.json'])
        ]
        
        # Mock relpath to return the expected relative path
        mock_relpath.return_value = 'package.json'
        
        # Simulate file read error
        mock_file_open.side_effect = IOError("Failed to read file")
        
        # Call event
        await create_initial_version(None, None, project)
        
        # Get created version
        versions = [obj for obj in mock_db_session.new if isinstance(obj, Version)]
        assert len(versions) == 1
        version = versions[0]
        
        # Verify version was still created
        assert version.project_id == project.id
        assert version.version_number == 0
        assert version.name == "Initial Version"
        
        # Verify no files were created
        files = [obj for obj in mock_db_session.new if isinstance(obj, File)]
        assert len(files) == 0
        
        # Verify session operations
        assert mock_db_session.commit.await_count == 2  # Initial commit and retry after error
        assert mock_db_session.refresh.await_count == 1  # For version
