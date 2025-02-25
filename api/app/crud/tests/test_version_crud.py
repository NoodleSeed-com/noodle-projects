"""Tests for version CRUD operations."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from ...models.version import Version
from ...models.project import Project
from ...schemas.common import FileChange, FileOperation
from ..version.crud import VersionCRUD

@pytest.mark.asyncio
async def test_get_next_version_number(mock_db_session):
    """Test getting the next version number."""
    # Setup
    project_id = uuid4()
    
    # Mock the database query result
    execute_result = AsyncMock()
    execute_result.scalar_one_or_none.return_value = 2  # Last version was 2
    mock_db_session.execute.return_value = execute_result
    
    # Get next version number
    result = await VersionCRUD.get_next_number(mock_db_session, project_id)
    
    # Verify result
    assert result == 3  # Should be 2 + 1
    
    # Verify query was called with correct parameters
    mock_db_session.execute.assert_called_once()
    call_args = mock_db_session.execute.call_args[0][0]
    assert str(project_id) in str(call_args)  # Project ID should be in the query

@pytest.mark.asyncio
async def test_get_next_version_number_no_versions(mock_db_session):
    """Test getting the next version number when no versions exist."""
    # Setup
    project_id = uuid4()
    
    # Mock the database query result - no versions exist
    execute_result = AsyncMock()
    execute_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = execute_result
    
    # Get next version number
    result = await VersionCRUD.get_next_number(mock_db_session, project_id)
    
    # Verify result
    assert result == 0  # Should be (-1) + 1 = 0

@pytest.mark.asyncio
async def test_get_version(mock_db_session, mock_project, mock_version, mock_files):
    """Test getting a specific version."""
    # Setup
    project_id = mock_project.id
    version_number = mock_version.version_number
    
    # Mock the database query result
    execute_result = AsyncMock()
    execute_result.unique.return_value = execute_result
    execute_result.scalar_one_or_none.return_value = mock_version
    mock_db_session.execute.return_value = execute_result
    
    # Mock the project active state query
    project_active_result = AsyncMock()
    project_active_result.scalar_one.return_value = True
    
    # Set up the execute mock to return different results based on the query
    def mock_execute(query):
        if "Project.active" in str(query):
            return project_active_result
        return execute_result
    
    mock_db_session.execute = AsyncMock(side_effect=mock_execute)
    
    # Get the version
    result = await VersionCRUD.get(mock_db_session, project_id, version_number)
    
    # Verify result
    assert result is not None
    assert result.id == mock_version.id
    assert result.project_id == project_id
    assert result.version_number == version_number
    assert result.name == mock_version.name
    assert len(result.files) == len(mock_files)
    assert result.active is True  # Project is active

@pytest.mark.asyncio
async def test_get_version_not_found(mock_db_session):
    """Test getting a version that doesn't exist."""
    # Setup
    project_id = uuid4()
    version_number = 1
    
    # Mock the database query result - version not found
    execute_result = AsyncMock()
    execute_result.unique.return_value = execute_result
    execute_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = execute_result
    
    # Get the version
    result = await VersionCRUD.get(mock_db_session, project_id, version_number)
    
    # Verify result
    assert result is None

@pytest.mark.asyncio
async def test_get_version_with_parent(mock_db_session, mock_project):
    """Test getting a version with a parent version."""
    # Setup
    project_id = mock_project.id
    
    # Create parent version
    parent_version = MagicMock(spec=Version)
    parent_version.id = uuid4()
    parent_version.project_id = project_id
    parent_version.version_number = 0
    parent_version.name = "Parent Version"
    parent_version.parent_id = None
    parent_version.files = []
    
    # Create child version
    child_version = MagicMock(spec=Version)
    child_version.id = uuid4()
    child_version.project_id = project_id
    child_version.version_number = 1
    child_version.name = "Child Version"
    child_version.parent_id = parent_version.id
    child_version.files = []
    
    # Mock the database query results
    version_result = AsyncMock()
    version_result.unique.return_value = version_result
    version_result.scalar_one_or_none.return_value = child_version
    
    parent_result = AsyncMock()
    parent_result.scalar_one_or_none.return_value = 0  # Parent version number
    
    project_active_result = AsyncMock()
    project_active_result.scalar_one.return_value = True
    
    # Set up the execute mock to return different results based on the query
    def mock_execute(query):
        if "Version.id" in str(query) and str(parent_version.id) in str(query):
            return parent_result
        elif "Project.active" in str(query):
            return project_active_result
        return version_result
    
    mock_db_session.execute = AsyncMock(side_effect=mock_execute)
    
    # Get the version
    result = await VersionCRUD.get(mock_db_session, project_id, 1)
    
    # Verify result
    assert result is not None
    assert result.id == child_version.id
    assert result.parent_id == parent_version.id
    assert result.parent_version == 0  # Parent version number

@pytest.mark.asyncio
async def test_get_multi(mock_db_session, mock_project, mock_version):
    """Test getting all versions of a project."""
    # Setup
    project_id = mock_project.id
    
    # Mock the project active state query
    project_active_result = AsyncMock()
    project_active_result.scalar_one.return_value = True
    
    # Mock the versions query result
    versions_result = AsyncMock()
    versions_result.all.return_value = [
        (mock_version.id, mock_version.version_number, mock_version.name)
    ]
    
    # Set up the execute mock to return different results based on the query
    def mock_execute(query):
        if "Project.active" in str(query):
            return project_active_result
        return versions_result
    
    mock_db_session.execute = AsyncMock(side_effect=mock_execute)
    
    # Get all versions
    result = await VersionCRUD.get_multi(mock_db_session, project_id)
    
    # Verify result
    assert len(result) == 1
    assert result[0].id == mock_version.id
    assert result[0].version_number == mock_version.version_number
    assert result[0].name == mock_version.name

@pytest.mark.asyncio
async def test_get_multi_inactive_project(mock_db_session, mock_project):
    """Test getting versions of an inactive project."""
    # Setup
    project_id = mock_project.id
    
    # Mock the project active state query - project is inactive
    project_active_result = AsyncMock()
    project_active_result.scalar_one.return_value = False
    mock_db_session.execute.return_value = project_active_result
    
    # Get all versions
    result = await VersionCRUD.get_multi(mock_db_session, project_id)
    
    # Verify result - should be empty list for inactive project
    assert len(result) == 0

@pytest.mark.asyncio
async def test_create_version(mock_db_session, mock_project, mock_version, mock_files, file_changes):
    """Test creating a new version with file changes."""
    # Setup
    project_id = mock_project.id
    parent_version_number = mock_version.version_number
    name = "New Version"
    
    # Mock the parent version query
    parent_version_result = AsyncMock()
    parent_version_result.unique.return_value = parent_version_result
    parent_version_result.scalar_one_or_none.return_value = mock_version
    
    # Mock the next version number query
    next_version_result = AsyncMock()
    next_version_result.scalar_one_or_none.return_value = 0
    
    # Set up the execute mock to return different results based on the query
    def mock_execute(query):
        if "order_by" in str(query) and "desc" in str(query):
            return next_version_result
        return parent_version_result
    
    mock_db_session.execute = AsyncMock(side_effect=mock_execute)
    
    # Mock the get method to return a response for the new version
    original_get = VersionCRUD.get
    VersionCRUD.get = AsyncMock()
    VersionCRUD.get.return_value = MagicMock(
        id=uuid4(),
        project_id=project_id,
        version_number=1,
        name=name,
        files=[]
    )
    
    # Create the new version
    result = await VersionCRUD.create(
        mock_db_session,
        project_id,
        parent_version_number,
        name,
        file_changes
    )
    
    # Restore the original get method
    VersionCRUD.get = original_get
    
    # Verify result
    assert result is not None
    assert result.project_id == project_id
    assert result.name == name
    
    # Verify the database operations
    assert mock_db_session.add.called
    assert mock_db_session.flush.called
    assert mock_db_session.refresh.called

@pytest.mark.asyncio
async def test_create_version_parent_not_found(mock_db_session):
    """Test creating a version when parent version is not found."""
    # Setup
    project_id = uuid4()
    parent_version_number = 0
    name = "New Version"
    changes = []
    
    # Mock the parent version query - parent not found
    parent_version_result = AsyncMock()
    parent_version_result.unique.return_value = parent_version_result
    parent_version_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = parent_version_result
    
    # Create the new version
    result = await VersionCRUD.create(
        mock_db_session,
        project_id,
        parent_version_number,
        name,
        changes
    )
    
    # Verify result
    assert result is None

@pytest.mark.asyncio
async def test_create_version_with_validation_error(mock_db_session, mock_project, mock_version, mock_files):
    """Test creating a version with invalid file changes."""
    # Setup
    project_id = mock_project.id
    parent_version_number = mock_version.version_number
    name = "New Version"
    
    # Invalid changes - trying to create a file that already exists
    existing_file_path = mock_files[0].path
    changes = [
        FileChange(
            operation=FileOperation.CREATE,
            path=existing_file_path,
            content="New content"
        )
    ]
    
    # Mock the parent version query
    parent_version_result = AsyncMock()
    parent_version_result.unique.return_value = parent_version_result
    parent_version_result.scalar_one_or_none.return_value = mock_version
    mock_db_session.execute.return_value = parent_version_result
    
    # Create the new version - should raise ValueError
    with pytest.raises(ValueError, match=f"Cannot create file that already exists: {existing_file_path}"):
        await VersionCRUD.create(
            mock_db_session,
            project_id,
            parent_version_number,
            name,
            changes
        )
