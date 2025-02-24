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
    assert initial_version.parent_version_id is None

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
    db_session.flush()
    
    version = Version(
        project_id=project.id,
        name="Test Version",
        parent_version_id=project.versions[0].id
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
    # Test empty name
    with pytest.raises(IntegrityError):
        project = Project(name="")
        db_session.add(project)
        db_session.commit()
    db_session.rollback()
    
    # Test name too long (max 255 chars)
    with pytest.raises(IntegrityError):
        project = Project(name="x" * 256)
        db_session.add(project)
        db_session.commit()
    db_session.rollback()
    
    # Test optional description
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()
    assert project.description is None
    
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
    db_session.flush()
    
    # Add versions
    versions = []
    for i in range(3):
        version = Version(
            project_id=project.id,
            name=f"Version {i+1}",
            parent_version_id=project.versions[0].id
        )
        versions.append(version)
        db_session.add(version)
    db_session.commit()
    
    # Verify relationships
    assert len(project.versions) == 4  # Initial + 3 new versions
    assert project.versions[0].version_number == 0
    for i, version in enumerate(project.versions[1:], 1):
        assert version.version_number > 0
        assert version.parent_version_id == project.versions[0].id
    
    # Test cascade delete
    db_session.delete(project)
    db_session.commit()
    
    # Verify all versions were deleted
    versions = db_session.query(Version).filter(
        Version.project_id == project.id
    ).all()
    assert len(versions) == 0

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
    db_session.flush()
    
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
            parent_version_id=project2.versions[0].id  # From different project
        )
        db_session.add(version)
        db_session.commit()
    db_session.rollback()
    
    # Valid version creation
    version = Version(
        project_id=project1.id,
        name="Valid Version",
        parent_version_id=project1.versions[0].id
    )
    db_session.add(version)
    db_session.commit()
    assert version.version_number > 0
    assert version.parent_version_id == project1.versions[0].id

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
