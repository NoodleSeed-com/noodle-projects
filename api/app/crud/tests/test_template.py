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
    """Test creating an initial version using a mocked template directory."""
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
    
    # Mock the TEMPLATE_PATH setting
    with patch('app.config.settings.TEMPLATE_PATH', new='/test/templates'):
        # Mock the file system operations
        template_files = [
            "package.json",
            "tsconfig.json",
            "public/index.html",
            "src/App.tsx",
            "src/index.tsx",
            "src/components/HelloWorld.tsx"
        ]
        
        template_dir = '/test/templates/version-0'
        
        # Create comprehensive mocks for all file system operations
        with patch('os.path.exists', return_value=True), \
             patch('os.walk') as mock_walk, \
             patch('os.path.join', side_effect=lambda *args: '/'.join(args)), \
             patch('os.path.relpath', side_effect=lambda path, start: path.replace(f"{template_dir}/", "")), \
             patch('builtins.open', mock_open(read_data="file content")), \
             patch('asyncio.to_thread', side_effect=lambda f: f()):
            
            # Setup mock_walk to return template files
            mock_walk.return_value = [
                (template_dir, [], template_files)
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
