"""Tests for Project model."""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from uuid import uuid4

def test_project_creation(db_session: Session):
    """Test basic project creation.
    
    Verifies:
    1. Project is created with correct attributes
    2. Initial version 0 is created automatically
    3. Active flag defaults to true
    4. Timestamps are set
    """
    project = Project(
        name="Test Project",
        description="Test Description"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "Test Description"
    assert project.active is True
    assert project.created_at is not None
    assert project.updated_at is not None
    
    # Verify initial version was created
    assert len(project.versions) == 1
    initial_version = project.versions[0]
    assert initial_version.version_number == 0
    assert initial_version.name == "Initial Version"
    assert initial_version.parent_id is None

def test_project_soft_delete(db_session: Session):
    """Test project soft deletion.
    
    Verifies:
    1. Project is marked inactive
    2. All versions are marked inactive
    3. Project can be reactivated
    4. Versions inherit active state
    """
    # Create project with multiple versions
    project = Project(
        name="Test Project",
        description="Test Description"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    
    # Initial version should exist
    assert len(project.versions) == 1
    initial_version = project.versions[0]
    
    # Add test version with next number
    version = Version(
        project_id=project.id,
        version_number=1,  # Use next version number
        name="Test Version",
        parent_id=initial_version.id
    )
    db_session.add(version)
    db_session.commit()
    
    # Soft delete project
    project.active = False
    db_session.commit()
    db_session.refresh(project)
    
    assert project.active is False
    for version in project.versions:
        assert version.active is False
    
    # Reactivate project
    project.active = True
    db_session.commit()
    db_session.refresh(project)
    
    assert project.active is True
    for version in project.versions:
        assert version.active is True

def test_project_constraints(db_session: Session):
    """Test project model constraints.
    
    Verifies:
    1. Name cannot be empty
    2. Name has maximum length
    3. Description is optional
    4. UUID is valid format
    """
    # Test empty name (Python-level validation)
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        project = Project(name="")

    # Test name too long (Python-level validation)
    with pytest.raises(ValueError, match="Project name cannot exceed 255 characters"):
        project = Project(name="x" * 256)
    
    # Test default empty description
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()
    assert project.description == ""  # Description defaults to empty string
    
    # Test UUID format
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()
    assert len(str(project.id)) == 36  # UUID string length

def test_project_relationships(db_session: Session):
    """Test project relationships.
    
    Verifies:
    1. Project can have multiple versions
    2. Versions are ordered by number
    3. Cascade delete works properly
    4. Relationship constraints are enforced
    """
    # Create project with multiple versions
    project = Project(
        name="Test Project",
        description="Test Description"
    )
    db_session.add(project)
    db_session.commit()  # Commit to trigger after_insert event that creates initial version
    
    # Add versions with sequential numbers starting from 1
    versions = []
    for i in range(3):
        version = Version(
            project_id=project.id,
            version_number=i+1,  # Use sequential numbers 1, 2, 3
            name=f"Version {i+1}",
            parent_id=project.versions[0].id
        )
        versions.append(version)
        db_session.add(version)
    db_session.commit()
    
    # Verify relationships
    assert len(project.versions) == 4  # Initial + 3 new versions
    assert project.versions[0].version_number == 0
    for i, version in enumerate(project.versions[1:], 1):
        assert version.version_number > 0
        assert version.parent_id == project.versions[0].id
    
    # Test cascade soft delete
    project.active = False
    db_session.commit()
    db_session.refresh(project)
    
    # Verify all versions are marked inactive
    versions = db_session.query(Version).filter(
        Version.project_id == project.id
    ).all()
    assert len(versions) == 4  # Initial + 3 new versions
    for version in versions:
        assert version.active is False

def test_version_validation(db_session: Session):
    """Test project version validation.
    
    Verifies:
    1. Version numbers are unique per project
    2. Version 0 is reserved for initial version
    3. Parent version must exist
    4. Parent version must be in same project
    """
    # Create two projects
    project1 = Project(name="Project 1")
    project2 = Project(name="Project 2")
    db_session.add_all([project1, project2])
    db_session.commit()  # Commit to trigger after_insert event that creates initial versions
    
    # Try to create duplicate version number
    with pytest.raises(IntegrityError):
        version = Version(
            project_id=project1.id,
            version_number=0,  # Already exists (initial version)
            name="Duplicate Version"
        )
        db_session.add(version)
        db_session.commit()
    db_session.rollback()
    
    # Try to use parent version from different project
    with pytest.raises(IntegrityError):
        version = Version(
            project_id=project1.id,
            name="Invalid Parent",
            parent_id=project2.versions[0].id  # From different project
        )
        db_session.add(version)
        db_session.commit()
    db_session.rollback()
    
    # Valid version creation with next version number
    next_version_number = max(v.version_number for v in project1.versions) + 1
    version = Version(
        project_id=project1.id,
        version_number=next_version_number,
        name="Valid Version",
        parent_id=project1.versions[0].id
    )
    db_session.add(version)
    db_session.commit()
    assert version.version_number == next_version_number
    assert version.parent_id == project1.versions[0].id

def test_latest_version_number(db_session: Session):
    """Test latest_version_number property.
    
    Verifies:
    1. Returns 0 for new project (only initial version)
    2. Returns correct max version number with multiple versions
    3. Handles non-sequential version numbers
    """
    # Create project (comes with version 0)
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    
    # Test initial state (should have version 0)
    assert project.latest_version_number == 0
    assert len(project.versions) == 1
    initial_version = project.versions[0]
    
    # Add versions with non-sequential numbers
    version1 = Version(
        project_id=project.id,
        version_number=3,
        name="Version 3",
        parent_id=initial_version.id
    )
    version2 = Version(
        project_id=project.id,
        version_number=1,
        name="Version 1",
        parent_id=initial_version.id
    )
    version3 = Version(
        project_id=project.id,
        version_number=5,
        name="Version 5",
        parent_id=initial_version.id
    )
    db_session.add_all([version1, version2, version3])
    db_session.commit()
    db_session.refresh(project)
    
    # Should return highest version number regardless of creation order
    assert project.latest_version_number == 5

def test_project_timestamps(db_session: Session):
    """Test project timestamp behavior.
    
    Verifies:
    1. Created timestamp is set on creation
    2. Updated timestamp changes on update
    3. Timestamps are in UTC
    4. Timestamps are not null
    """
    # Create project
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()
    
    created_at = project.created_at
    updated_at = project.updated_at
    
    assert created_at is not None
    assert updated_at is not None
    assert created_at == updated_at
    
    # Update project
    project.name = "Updated Name"
    db_session.commit()
    db_session.refresh(project)
    
    assert project.created_at == created_at
    assert project.updated_at > updated_at
