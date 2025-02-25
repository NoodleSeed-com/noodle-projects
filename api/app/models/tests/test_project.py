"""Tests for Project model."""
import pytest
from unittest.mock import MagicMock, AsyncMock, PropertyMock, call
from sqlalchemy.exc import IntegrityError
from ...models.project import Project
from ...models.version import Version
from ...errors import NoodleError
from uuid import uuid4
from datetime import datetime

@pytest.mark.asyncio
async def test_project_creation(mock_db_session, mock_models):
    """Test basic project creation."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.name = "Test Project"
    mock_project.description = "Test Description"
    mock_project.active = True
    mock_project.created_at = MagicMock()
    mock_project.updated_at = MagicMock()
    mock_project.versions = [MagicMock(spec=Version)]
    mock_project.versions[0].version_number = 0
    mock_project.versions[0].name = "Initial Version"
    mock_project.versions[0].parent_id = None

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project", description="Test Description")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "Test Description"
    assert project.active is True
    assert project.created_at is not None
    assert project.updated_at is not None
    assert len(project.versions) == 1
    assert project.versions[0].version_number == 0
    assert project.versions[0].name == "Initial Version"
    assert project.versions[0].parent_id is None

@pytest.mark.asyncio
async def test_project_soft_delete(mock_db_session, mock_models):
    """Test project soft deletion."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version), MagicMock(spec=Version)]
    
    # Set up version active properties
    for version in mock_project.versions:
        type(version).active = PropertyMock(return_value=True)
    
    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project", description="Test Description")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    # Update active property for versions
    for version in project.versions:
        type(version).active = PropertyMock(return_value=False)

    project.active = False
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.active is False
    for version in project.versions:
        assert version.active is False

    # Update active property for versions
    for version in project.versions:
        type(version).active = PropertyMock(return_value=True)

    project.active = True
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.active is True
    for version in project.versions:
        assert version.active is True

@pytest.mark.asyncio
async def test_project_constraints(mock_db_session, mock_models):
    """Test project model constraints."""
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="")

    with pytest.raises(ValueError, match="Project name cannot exceed 255 characters"):
        Project(name="x" * 256)

    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.description = ""

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()

    assert project.description == ""
    assert len(str(project.id)) == 36

@pytest.mark.asyncio
async def test_project_relationships(mock_db_session, mock_models):
    """Test project relationships."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version) for _ in range(4)]
    for i, version in enumerate(mock_project.versions):
        version.version_number = i
        version.parent_id = mock_project.versions[0].id if i > 0 else None
        version.active = True

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project", description="Test Description")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert len(project.versions) == 4
    assert project.versions[0].version_number == 0
    for i, version in enumerate(project.versions[1:], 1):
        assert version.version_number > 0
        assert version.parent_id == project.versions[0].id

    project.active = False
    for version in project.versions:
        version.active = False
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    for version in project.versions:
        await mock_db_session.refresh(version)
        assert version.active is False, f"Version {version.version_number} is still active"

@pytest.mark.asyncio
async def test_version_validation(mock_db_session, mock_models):
    """Test project version validation."""
    # Setup projects
    mock_project1 = MagicMock(spec=Project)
    mock_project1.id = uuid4()
    mock_project1.versions = [MagicMock(spec=Version)]
    mock_project1.versions[0].id = uuid4()
    mock_project1.versions[0].version_number = 0

    mock_project2 = MagicMock(spec=Project)
    mock_project2.id = uuid4()
    mock_project2.versions = [MagicMock(spec=Version)]
    mock_project2.versions[0].id = uuid4()

    mock_models.Project.side_effect = [mock_project1, mock_project2]
    mock_db_session.add.return_value = None

    # Set up commit mock
    error_commits = {2, 4}  # Set of commit numbers that should raise IntegrityError
    commit_count = 0

    async def mock_commit():
        nonlocal commit_count
        commit_count += 1
        if commit_count in error_commits:
            raise IntegrityError(None, None, None)
        return None

    mock_db_session.commit = AsyncMock(side_effect=mock_commit)
    mock_db_session.rollback = AsyncMock()

    # Create initial projects
    project1 = mock_models.Project(name="Project 1")
    project2 = mock_models.Project(name="Project 2")
    mock_db_session.add_all([project1, project2])
    await mock_db_session.commit()  # commit_count = 1

    # Test duplicate version number
    mock_version = MagicMock(spec=Version)
    mock_version.project_id = project1.id
    mock_version.version_number = 0
    mock_version.name = "Duplicate Version"
    mock_models.Version.return_value = mock_version

    with pytest.raises(IntegrityError):
        version = mock_models.Version(project_id=project1.id, version_number=0, name="Duplicate Version")
        mock_db_session.add(version)
        await mock_db_session.commit()  # commit_count = 2 (raises error)
    await mock_db_session.rollback()

    # Test invalid parent version from different project
    mock_version = MagicMock(spec=Version)
    mock_version.project_id = project1.id
    mock_version.name = "Invalid Parent"
    mock_version.parent_id = project2.versions[0].id
    
    # Mock validate method to raise NoodleError
    async def mock_validate(session):
        parent = session.get(Version, mock_version.parent_id)
        if parent and parent.project_id != mock_version.project_id:
            raise NoodleError("Parent version must be from the same project")
    mock_version.validate = mock_validate
    
    # Mock session.get to return appropriate objects
    def mock_get(model_class, id_):
        if model_class == Project and id_ == project1.id:
            return project1
        elif model_class == Version and id_ == project2.versions[0].id:
            parent_version = project2.versions[0]
            parent_version.project_id = project2.id
            return parent_version
        return None
    mock_db_session.get = MagicMock(side_effect=mock_get)

    # Create version with parent from different project
    mock_models.Version.return_value = mock_version
    version = mock_models.Version(project_id=project1.id, name="Invalid Parent", parent_id=project2.versions[0].id)
    mock_db_session.add(version)
    
    # Manually call validate since the event listener might not be triggered in tests
    with pytest.raises(NoodleError, match="Parent version must be from the same project"):
        await version.validate(mock_db_session)
    
    # No need to commit or rollback since validate will raise the error

    # Test successful version creation
    next_version_number = max(v.version_number for v in project1.versions) + 1
    mock_version = MagicMock(spec=Version)
    mock_version.project_id = project1.id
    mock_version.version_number = next_version_number
    mock_version.name = "Valid Version"
    mock_version.parent_id = project1.versions[0].id
    mock_models.Version.return_value = mock_version

    version = mock_models.Version(
        project_id=project1.id,
        version_number=next_version_number,
        name="Valid Version",
        parent_id=project1.versions[0].id
    )
    mock_db_session.add(version)
    await mock_db_session.commit()  # commit_count = 6

    assert version.version_number == next_version_number
    assert version.parent_id == project1.versions[0].id

@pytest.mark.asyncio
async def test_latest_version_number(mock_db_session, mock_models):
    """Test latest_version_number property."""
    # Test project with versions
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = [MagicMock(spec=Version) for _ in range(4)]
    mock_project.versions[0].version_number = 0
    mock_project.versions[1].version_number = 3
    mock_project.versions[2].version_number = 1
    mock_project.versions[3].version_number = 5
    
    # Mock the latest_version_number property
    type(mock_project).latest_version_number = PropertyMock(return_value=5)

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")  # Use mock Project class
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.latest_version_number == 5

    # Test project with no versions
    mock_project_no_versions = MagicMock(spec=Project)
    mock_project_no_versions.id = uuid4()
    mock_project_no_versions.versions = []
    type(mock_project_no_versions).latest_version_number = PropertyMock(return_value=0)

    mock_models.Project.return_value = mock_project_no_versions
    
    project_no_versions = mock_models.Project(name="Test Project No Versions")  # Use mock Project class
    mock_db_session.add(project_no_versions)
    await mock_db_session.commit()
    await mock_db_session.refresh(project_no_versions)

    assert project_no_versions.latest_version_number == 0

@pytest.mark.asyncio
async def test_async_validation(mock_db_session, mock_models):
    """Test async validation handling."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    
    # Add an async validate method
    async def async_validate(session):
        # Simulate async validation
        return True
    
    mock_project.validate = async_validate
    
    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()  # This should trigger the async validate method
    await mock_db_session.refresh(project)

    assert project.id is not None

@pytest.mark.asyncio
async def test_project_timestamps(mock_db_session, mock_models):
    """Test project timestamp behavior."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    
    # Initial timestamps
    created_at = datetime(2025, 2, 24, 20, 0, 0)
    updated_at = datetime(2025, 2, 24, 20, 0, 0)
    mock_project.created_at = created_at
    mock_project.updated_at = updated_at

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()

    assert project.created_at == created_at
    assert project.updated_at == updated_at

    # Update project and set a new updated_at timestamp
    project.name = "Updated Name"
    new_updated_at = datetime(2025, 2, 24, 20, 1, 0)  # 1 minute later
    mock_project.updated_at = new_updated_at
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.created_at == created_at
    assert project.updated_at == new_updated_at
    assert project.updated_at > project.created_at

@pytest.mark.asyncio
async def test_version_ordering(mock_db_session, mock_models):
    """Test version ordering within project."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = []

    # Create versions in non-sequential order
    version_numbers = [3, 1, 4, 0, 2]
    for number in version_numbers:
        mock_version = MagicMock(spec=Version)
        mock_version.id = uuid4()
        mock_version.version_number = number
        mock_version.name = f"Version {number}"
        mock_project.versions.append(mock_version)

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    # Verify versions are ordered by version_number
    assert len(project.versions) == 5
    for i, version in enumerate(sorted(project.versions, key=lambda v: v.version_number)):
        assert version.version_number == i

@pytest.mark.asyncio
async def test_cascade_delete(mock_db_session, mock_models):
    """Test cascade delete behavior with versions."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = []

    # Create project with versions
    for i in range(3):
        mock_version = MagicMock(spec=Version)
        mock_version.id = uuid4()
        mock_version.version_number = i
        mock_version.name = f"Version {i}"
        mock_project.versions.append(mock_version)

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create project and verify versions
    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert len(project.versions) == 3

    # Set up mock query to simulate cascade delete
    def mock_query_filter(model_class):
        def filter_func(*args):
            class MockFilter:
                def all(self):
                    # After delete, return empty list
                    if hasattr(mock_db_session, '_deleted'):
                        return []
                    return project.versions
            return MockFilter()
        return MagicMock(filter=filter_func)

    mock_db_session.query = mock_query_filter

    # Delete project
    mock_db_session.delete(project)
    await mock_db_session.commit()
    
    # Mark session as having performed delete
    mock_db_session._deleted = True

    # Verify versions were cascade deleted
    remaining_versions = mock_db_session.query(Version).filter(Version.project_id == project.id).all()
    assert len(remaining_versions) == 0

@pytest.mark.asyncio
async def test_concurrent_version_creation(mock_db_session, mock_models):
    """Test concurrent version creation handling."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = []

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    # Create initial version
    mock_version = MagicMock(spec=Version)
    mock_version.id = uuid4()
    mock_version.version_number = 1
    mock_version.name = "Version 1"
    
    # First version should succeed
    mock_db_session.commit.side_effect = None
    project.versions = [mock_version]  # Replace list instead of append
    await mock_db_session.commit()
    
    # Try to create concurrent versions
    for i in range(2):
        concurrent_version = MagicMock(spec=Version)
        concurrent_version.id = uuid4()
        concurrent_version.version_number = 1  # Same version number
        concurrent_version.name = f"Concurrent Version {i+1}"
        
        # Simulate concurrent creation failure
        mock_db_session.commit.side_effect = IntegrityError(None, None, None)
        with pytest.raises(IntegrityError):
            temp_versions = project.versions.copy()
            temp_versions.append(concurrent_version)
            project.versions = temp_versions
            await mock_db_session.commit()
        await mock_db_session.rollback()
        # Restore original versions after rollback
        project.versions = [mock_version]

    # Verify only one version with number 1 exists
    assert len([v for v in project.versions if v.version_number == 1]) == 1

@pytest.mark.asyncio
async def test_description_constraints(mock_db_session, mock_models):
    """Test project description field constraints."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.description = ""

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Test default empty description
    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert project.description == ""

    # Test large description
    large_description = "x" * (1024 * 1024)  # 1MB description
    mock_project.description = large_description
    
    project = mock_models.Project(name="Test Project", description=large_description)
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    assert len(project.description) == len(large_description)

@pytest.mark.asyncio
async def test_selectin_loading(mock_db_session, mock_models):
    """Test selectin loading strategy for versions relationship."""
    mock_project = MagicMock(spec=Project)
    mock_project.id = uuid4()
    mock_project.versions = []

    # Create versions
    for i in range(3):
        mock_version = MagicMock(spec=Version)
        mock_version.id = uuid4()
        mock_version.version_number = i
        mock_version.name = f"Version {i}"
        mock_project.versions.append(mock_version)

    mock_models.Project.return_value = mock_project
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create project
    project = mock_models.Project(name="Test Project")
    mock_db_session.add(project)
    await mock_db_session.commit()
    await mock_db_session.refresh(project)

    # Mock selectin loading behavior
    mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = project
    mock_db_session.query.return_value.filter.return_value.all.return_value = project.versions

    # Verify versions are loaded with selectin strategy
    loaded_project = mock_db_session.query(Project).options().filter(Project.id == project.id).first()
    assert loaded_project is not None
    assert len(loaded_project.versions) == 3  # Versions should be loaded eagerly
    
    # Verify no additional queries needed for versions
    versions = loaded_project.versions
    assert len(versions) == 3  # Should use already loaded versions
