import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime

from app.crud.project import ProjectCRUD
from app.models.project import Project, ProjectCreate, ProjectUpdate

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_project():
    """Test creating a project."""
    # Arrange
    mock_db = AsyncMock()
    project_data = ProjectCreate(name="Test Project", description="Test Description")
    
    # Mock db.commit to do nothing
    mock_db.commit = AsyncMock()
    
    # Mock db.refresh to set fields
    async def mock_refresh(obj):
        obj.id = uuid.uuid4()
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()
        obj.active = True
        return obj
    
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    
    # Act
    result = await ProjectCRUD.create(db=mock_db, project=project_data)
    
    # Assert
    assert result is not None
    assert result.name == "Test Project"
    assert result.description == "Test Description"
    assert result.active is True
    assert result.id is not None
    assert result.created_at is not None
    assert result.updated_at is not None
    
    # Verify db interactions
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_project():
    """Test getting a project by ID."""
    # Arrange
    mock_db = AsyncMock()
    project_id = uuid.uuid4()
    
    # Create a mock project
    mock_project = Project(
        id=project_id,
        name="Test Project",
        description="Test Description",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Mock the chain of methods that get called
    mock_unique = MagicMock()
    mock_unique.scalar_one_or_none.return_value = mock_project
    
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_unique
    
    # Configure execute to return our mock_result
    mock_db.execute.return_value = mock_result
    
    # Act
    result = await ProjectCRUD.get(db=mock_db, project_id=project_id)
    
    # Assert
    assert result is not None
    assert result is mock_project  # Should be the same object
    assert result.id == project_id
    assert result.name == "Test Project"
    assert result.description == "Test Description"
    assert result.active is True
    
    # Verify db interactions
    mock_db.execute.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_project():
    """Test updating a project."""
    # Arrange
    mock_db = AsyncMock()
    project_id = uuid.uuid4()
    
    # Create a mock project with the updated values
    updated_project = Project(
        id=project_id,
        name="Updated Name",  # This is the updated value
        description="Original Description", 
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Mock scalar_one_or_none to return the updated project
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = updated_project
    
    # Configure execute to return our mock_result
    mock_db.execute.return_value = mock_result
    
    # Create update data
    project_data = ProjectUpdate(name="Updated Name")
    
    # Act
    result = await ProjectCRUD.update(db=mock_db, project_id=project_id, project=project_data)
    
    # Assert
    assert result is not None
    assert result is updated_project  # Should be the same object
    assert result.id == project_id
    assert result.name == "Updated Name"  # Should be updated
    assert result.description == "Original Description"  # Should be unchanged
    assert result.active is True  # Should be unchanged
    
    # Verify db interactions
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()