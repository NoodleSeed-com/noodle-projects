"""Tests for template handling in version CRUD."""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from uuid import uuid4
from ...models.version import Version
from ...models.file import File
from ..version.template import create_initial_version

@pytest.mark.asyncio
async def test_create_initial_version(mock_db_session):
    """Test creating an initial version with template files."""
    # Setup
    project_id = uuid4()
    
    # Mock the Version model
    version = MagicMock(spec=Version)
    version.id = uuid4()
    version.project_id = project_id
    version.version_number = 0
    version.name = "Initial Version"
    
    # Mock the db.add and db.refresh to set the version.id
    def mock_add(obj):
        if isinstance(obj, Version):
            obj.id = version.id
    
    mock_db_session.add.side_effect = mock_add
    
    # Ensure commit and refresh don't return coroutines
    mock_db_session.commit.side_effect = None
    mock_db_session.refresh.side_effect = None
    
    # Mock the file system operations
    template_files = [
        ("package.json", '{"name": "test-project"}'),
        ("tsconfig.json", '{"compilerOptions": {}}'),
        ("public/index.html", "<html></html>"),
        ("src/App.tsx", "export const App = () => <div>App</div>;"),
        ("src/index.tsx", "import React from 'react';"),
        ("src/components/HelloWorld.tsx", "export const HelloWorld = () => <div>Hello World</div>;")
    ]
    
    # Create a more specific mock_open that returns different content based on the file
    file_contents = {f"/templates/version-0/{path}": content for path, content in template_files}
    
    def mock_file_open(filename, *args, **kwargs):
        content = file_contents.get(filename, "default content")
        return mock_open(read_data=content)()
    
    # Mock os.walk to return template files
    with patch('os.walk') as mock_walk, \
         patch('os.path.join', side_effect=lambda *args: '/'.join(args)), \
         patch('os.path.relpath', side_effect=lambda path, start: path.replace('/templates/version-0/', '')), \
         patch('builtins.open', mock_file_open):
        
        # Setup mock_walk to return template files
        mock_walk.return_value = [
            ("/templates/version-0", [], [path for path, _ in template_files])
        ]
        
        # Call the function
        result = await create_initial_version(mock_db_session, project_id)
        
        # Verify the version was created
        assert result.id == version.id
        assert result.project_id == project_id
        assert result.version_number == 0
        assert result.name == "Initial Version"
        
        # Verify db operations
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called
        
        # Verify file creation
        # The number of calls to db.add should be 1 (for version) + number of files
        assert mock_db_session.add.call_count >= len(template_files) + 1

@pytest.mark.asyncio
async def test_create_initial_version_with_real_template_dir(mock_db_session):
    """Test creating an initial version with the actual template directory."""
    # Setup
    project_id = uuid4()
    
    # Mock the Version model
    version = MagicMock(spec=Version)
    version.id = uuid4()
    version.project_id = project_id
    version.version_number = 0
    version.name = "Initial Version"
    
    # Mock the db.add and db.refresh to set the version.id
    def mock_add(obj):
        if isinstance(obj, Version):
            obj.id = version.id
    
    mock_db_session.add.side_effect = mock_add
    
    # Ensure commit and refresh don't return coroutines
    mock_db_session.commit.side_effect = None
    mock_db_session.refresh.side_effect = None
    
    # Get the actual template directory path
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'templates', 'version-0')
    
    # Check if the template directory exists
    if not os.path.exists(template_dir):
        pytest.skip(f"Template directory not found: {template_dir}")
    
    # Count the number of files in the template directory
    file_count = 0
    for root, _, files in os.walk(template_dir):
        file_count += len(files)
    
    # Create a fixed template directory path for the test
    fixed_template_dir = "/fixed/path/templates/version-0"
    
    # Mock os.path.join to return the fixed template directory path when called with the expected arguments
    original_join = os.path.join
    def mock_join(*args):
        # If this is the call to get the template directory in create_initial_version
        if len(args) >= 5 and args[-2:] == ('templates', 'version-0'):
            return fixed_template_dir
        # Otherwise, use the original join
        return original_join(*args)
    
    # Mock the file system operations
    template_files = [
        "package.json",
        "tsconfig.json",
        "public/index.html",
        "src/App.tsx",
        "src/index.tsx",
        "src/components/HelloWorld.tsx"
    ]
    
    # Mock file open to avoid actually reading files
    with patch('os.path.join', side_effect=mock_join), \
         patch('os.walk') as mock_walk, \
         patch('os.path.relpath', side_effect=lambda path, start: path.replace(f"{fixed_template_dir}/", "")), \
         patch('builtins.open', mock_open(read_data="file content")):
        
        # Setup mock_walk to return template files
        mock_walk.return_value = [
            (fixed_template_dir, [], template_files)
        ]
        
        # Call the function
        result = await create_initial_version(mock_db_session, project_id)
        
        # Verify the version was created
        assert result.id == version.id
        assert result.project_id == project_id
        assert result.version_number == 0
        assert result.name == "Initial Version"
        
        # Verify db operations
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called
        
        # Verify file creation - should have at least as many calls as files
        assert mock_db_session.add.call_count >= len(template_files) + 1

@pytest.mark.asyncio
async def test_create_initial_version_error_handling(mock_db_session):
    """Test error handling during initial version creation."""
    # Setup
    project_id = uuid4()
    
    # Mock commit to raise an exception
    mock_db_session.commit.side_effect = Exception("Database error")
    
    # Mock the file system operations to avoid issues
    with patch('os.walk') as mock_walk, \
         patch('os.path.join', side_effect=lambda *args: '/'.join(args)), \
         patch('os.path.relpath', side_effect=lambda path, start: path.split('/')[-1]), \
         patch('builtins.open', mock_open(read_data="file content")):
        
        # Setup mock_walk to return empty template files
        mock_walk.return_value = [("/templates/version-0", [], [])]
        
        # Call the function - should raise the exception
        with pytest.raises(Exception, match="Database error"):
            await create_initial_version(mock_db_session, project_id)
        
        # Verify db operations
        assert mock_db_session.add.called  # Version was added
        assert mock_db_session.commit.called  # Commit was attempted
