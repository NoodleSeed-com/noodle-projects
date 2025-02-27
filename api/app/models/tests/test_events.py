"""Test SQLAlchemy event listeners."""
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from uuid import uuid4

from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from ...crud.version.template import create_initial_version
from ...errors import NoodleError

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
        await create_initial_version(mock_db_session, project.id)
        
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
    """Test that a version is created even when project is not already in session."""
    project = Project(id=uuid4(), name="Test Project")
    # Don't add to session
    
    # Instead of mocking internal functions, just mock os.walk to return no files
    with patch('os.walk') as mock_walk:
        # Set up os.walk to return no files (empty template directory)
        mock_walk.return_value = []
        
        # Call event directly
        await create_initial_version(mock_db_session, project.id)
        
        # Verify a version was created
        versions = [obj for obj in mock_db_session.new if isinstance(obj, Version)]
        assert len(versions) == 1
        
        # Verify the version properties
        version = versions[0]
        assert version.project_id == project.id
        assert version.version_number == 0

@pytest.mark.asyncio
async def test_create_initial_version_file_error(mock_db_session):
    """Test handling of file read errors."""
    # Create a project with mock session
    project = Project(id=uuid4(), name="Test Project")
    project._sa_session = mock_db_session
    mock_db_session.add(project)
    
    # Patch builtins.open directly to simulate file error
    # This will happen inside the read_file function
    with patch('builtins.open', create=True) as mock_open:
        # Set up open to raise an IOError when called
        mock_open.side_effect = IOError("Failed to read file")
        
        # We also need to patch os.walk to return some files
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/mock/path/templates/version-0', [], ['package.json'])
            ]
            
            # Make sure path operations return something reasonable
            with patch('os.path.dirname') as mock_dirname, \
                 patch('os.path.join') as mock_join, \
                 patch('os.path.relpath') as mock_relpath:
                
                mock_dirname.return_value = '/mock/path'
                mock_join.side_effect = lambda *args: '/'.join(args)
                mock_relpath.return_value = 'package.json'
                
                # We need a try/except block since the function will raise an error
                try:
                    await create_initial_version(mock_db_session, project.id)
                    # If we reach here, the test fails - should have raised an exception
                    assert False, "Expected IOError was not raised"
                except IOError as e:
                    # This is expected
                    assert "Failed to read file" in str(e)
                
                # Verify that the version was created before the error
                # In the real function, the version is committed before file processing
                assert mock_db_session.commit.await_count >= 1
                assert mock_db_session.refresh.await_count >= 1
            
@pytest.mark.asyncio
async def test_version_validate_before_commit(mock_db_session):
    """Test version validation during before_commit event."""
    # Create a project first
    project_id = uuid4()
    project = Project(id=project_id, name="Test Project", active=True)
    
    # Mock the get method to return our objects based on ID
    objects_by_id = {project_id: project}
    
    # Create a valid version
    valid_version_id = uuid4()
    valid_version = Version(
        project_id=project_id,
        version_number=0,
        name="Valid Version"
    )
    valid_version.id = valid_version_id
    objects_by_id[valid_version_id] = valid_version
    
    # Create a version with an invalid parent (from different project)
    other_project_id = uuid4()
    other_project = Project(id=other_project_id, name="Other Project", active=True)
    objects_by_id[other_project_id] = other_project
    
    other_version_id = uuid4()
    other_version = Version(
        project_id=other_project_id, 
        version_number=0,
        name="Other Version"
    )
    other_version.id = other_version_id
    objects_by_id[other_version_id] = other_version
    
    # This version has a parent from a different project
    invalid_version = Version(
        project_id=project_id,
        version_number=1,
        parent_id=other_version_id,
        name="Invalid Version"
    )
    mock_db_session.add(invalid_version)
    
    # Mock the session.get method to return our stored objects
    def mock_get(model_class, id_value):
        return objects_by_id.get(id_value)
    
    mock_db_session.get.side_effect = mock_get
    
    # Directly test the validate method
    with pytest.raises(NoodleError) as exc_info:
        invalid_version.validate(mock_db_session)
    
    # Verify error message
    assert "Parent version must be from the same project" in str(exc_info.value)
    
@pytest.mark.asyncio
async def test_version_active_property():
    """Test that the version active property inherits from project."""
    # Create project and version without session
    project = Project(id=uuid4(), name="Test Project", active=True)
    version = Version(project_id=project.id, version_number=0, name="Test Version")
    
    # Link them manually for testing the property
    version.project = project
    
    # Test active property inheritance when project is active
    assert version.active is True
    
    # Change project status and verify version reflects it
    project.active = False
    assert version.active is False
    
@pytest.mark.asyncio
async def test_version_constructor_validation():
    """Test version constructor validation."""
    # Test validation in constructor - project_id is required
    with pytest.raises(NoodleError) as exc_info:
        Version()
    assert "project_id is required" in str(exc_info.value)
    
    # Test negative version number validation
    project_id = uuid4()
    with pytest.raises(NoodleError) as exc_info:
        Version(project_id=project_id, version_number=-1)
    assert "Version number cannot be negative" in str(exc_info.value)
    
    # Test default version number
    version = Version(project_id=project_id)
    assert version.version_number == 0
