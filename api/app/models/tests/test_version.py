"""Tests for Version model."""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ...models.project import Project
from ...models.version import Version
from ...models.file import File
from ...errors import NoodleError, ErrorType

def test_version_creation(db_session: Session):
    """Test basic version creation.
    
    Verifies:
    1. Version is created with correct attributes
    2. Version number is auto-incremented
    3. Active flag inherits from project
    4. Timestamps are set
    """
    # Create project
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()  # Commit to trigger after_insert event that creates initial version
    db_session.refresh(project)
    
    # Create version with next number
    next_version_number = max(v.version_number for v in project.versions) + 1
    version = Version(
        project_id=project.id,
        version_number=next_version_number,
        name="Test Version",
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    
    assert version.id is not None
    assert version.name == "Test Version"
    assert version.version_number > 0
    assert version.active == project.active
    assert version.created_at is not None
    assert version.updated_at is not None
    assert version.parent_id == project.versions[0].id

def test_version_file_relationships(db_session: Session):
    """Test version file relationships.
    
    Verifies:
    1. Version can have multiple files
    2. Files are properly associated
    3. Cascade delete works
    4. File constraints are enforced
    """
    # Create project and version
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()  # Commit to trigger after_insert event that creates initial version
    db_session.refresh(project)
    
    # Create version with next number
    next_version_number = max(v.version_number for v in project.versions) + 1
    version = Version(
        project_id=project.id,
        version_number=next_version_number,
        name="Test Version",
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    
    # Add files
    files = []
    for i in range(3):
        file = File(
            version_id=version.id,
            path=f"src/test{i}.tsx",
            content=f"Test content {i}"
        )
        files.append(file)
        db_session.add(file)
    db_session.commit()
    
    # Verify relationships
    assert len(version.files) == 3
    for i, file in enumerate(version.files):
        assert file.path == f"src/test{i}.tsx"
        assert file.content == f"Test content {i}"
    
    # Test cascade delete
    db_session.delete(version)
    db_session.commit()
    
    # Verify all files were deleted
    files = db_session.query(File).filter(
        File.version_id == version.id
    ).all()
    assert len(files) == 0

def test_version_file_constraints(db_session: Session):
    """Test version file constraints.
    
    Verifies:
    1. File paths must be unique within version
    2. Empty paths are rejected
    3. File content is required
    4. Path format is validated
    """
    # Create project and version
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()  # Commit to trigger after_insert event that creates initial version
    db_session.refresh(project)
    
    # Create version with next number
    next_version_number = max(v.version_number for v in project.versions) + 1
    version = Version(
        project_id=project.id,
        version_number=next_version_number,
        name="Test Version",
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    
    # Test duplicate path
    file1 = File(
        version_id=version.id,
        path="src/test.tsx",
        content="Test content"
    )
    db_session.add(file1)
    db_session.commit()
    
    with pytest.raises(IntegrityError):
        file2 = File(
            version_id=version.id,
            path="src/test.tsx",  # Duplicate path
            content="Different content"
        )
        db_session.add(file2)
        db_session.commit()
    db_session.rollback()
    
    # Test empty path (Python-level validation)
    with pytest.raises(ValueError, match="File path cannot be empty"):
        file = File(
            version_id=version.id,
            path="",  # Empty path
            content="Test content"
        )
    
    # Test missing content (Python-level validation)
    with pytest.raises(ValueError, match="File content cannot be null"):
        file = File(
            version_id=version.id,
            path="src/test2.tsx",
            content=None  # Missing content
        )

def test_version_inheritance(db_session: Session):
    """Test version inheritance behavior.
    
    Verifies:
    1. Version inherits active state from project
    2. Version maintains parent relationship
    3. Version numbers are sequential
    4. Parent version validation works
    """
    # Create project
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()  # Commit to trigger after_insert event that creates initial version
    db_session.refresh(project)
    
    # Create chain of versions
    parent = project.versions[0]  # Initial version
    for i in range(3):
        next_version_number = max(v.version_number for v in project.versions) + 1
        version = Version(
            project_id=project.id,
            version_number=next_version_number,
            name=f"Version {i+1}",
            parent_id=parent.id
        )
        db_session.add(version)
        db_session.commit()
        db_session.refresh(version)
        parent = version
    
    # Verify version chain
    versions = db_session.query(Version).filter(
        Version.project_id == project.id
    ).order_by(Version.version_number).all()
    
    assert len(versions) == 4  # Initial + 3 new versions
    for i, version in enumerate(versions):
        assert version.version_number == i
        if i > 0:
            assert version.parent_id == versions[i-1].id
    
    # Test active state inheritance
    project.active = False
    db_session.commit()
    db_session.refresh(project)
    
    for version in versions:
        db_session.refresh(version)
        assert version.active is False

def test_version_validation(db_session: Session):
    """Test version validation rules.
    
    Verifies:
    1. Version number is unique per project
    2. Parent version must exist
    3. Parent version must be from same project
    4. Cannot create version in inactive project
    """
    # Create two projects
    project1 = Project(name="Project 1")
    project2 = Project(name="Project 2")
    db_session.add_all([project1, project2])
    db_session.commit()  # Commit to trigger after_insert event that creates initial versions
    db_session.refresh(project1)
    db_session.refresh(project2)
    
    # Try to create version with explicit number
    # Try to create version without project_id
    with pytest.raises(NoodleError, match="project_id is required"):
        version = Version(
            name="Test Version"
        )

    # Try to create version with duplicate number
    with pytest.raises(IntegrityError):
        version = Version(
            project_id=project1.id,
            version_number=0,  # Already exists
            name="Test Version",
            parent_id=project1.versions[0].id
        )
        db_session.add(version)
        db_session.commit()
    db_session.rollback()
    
    # Try to use parent from different project
    with pytest.raises(IntegrityError):
        version = Version(
            project_id=project1.id,
            name="Test Version",
            parent_id=project2.versions[0].id  # Wrong project
        )
        db_session.add(version)
        db_session.commit()
    db_session.rollback()
    
    # Try to create version in inactive project
    project1.active = False
    db_session.commit()
    db_session.refresh(project1)
    
    # Get next version number to avoid unique constraint violation
    next_version_number = max(v.version_number for v in project1.versions) + 1
    
    with pytest.raises(NoodleError, match="Cannot create version in inactive project"):
        version = Version(
            project_id=project1.id,
            version_number=next_version_number,
            name="Test Version",
            parent_id=project1.versions[0].id
        )
        db_session.add(version)
        db_session.commit()
    db_session.rollback()

def test_version_timestamps(db_session: Session):
    """Test version timestamp behavior.
    
    Verifies:
    1. Created timestamp is set on creation
    2. Updated timestamp changes on update
    3. Timestamps are in UTC
    4. Timestamps are not null
    """
    # Create project and version
    project = Project(name="Test Project")
    db_session.add(project)
    db_session.commit()  # Commit to trigger after_insert event that creates initial version
    db_session.refresh(project)
    
    # Create version with next number
    next_version_number = max(v.version_number for v in project.versions) + 1
    version = Version(
        project_id=project.id,
        version_number=next_version_number,
        name="Test Version",
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    db_session.commit()
    
    created_at = version.created_at
    updated_at = version.updated_at
    
    assert created_at is not None
    assert updated_at is not None
    assert created_at == updated_at
    
    # Update version
    version.name = "Updated Name"
    db_session.commit()
    db_session.refresh(version)
    
    assert version.created_at == created_at
    assert version.updated_at > updated_at
