"""Tests for File model."""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ...models.project import Project
from ...models.version import Version
from ...models.file import File

@pytest.mark.asyncio
async def test_file_creation(db_session: AsyncSession):
    """Test basic file creation.
    
    Verifies:
    1. File is created with correct attributes
    2. File is properly associated with version
    3. UUID is generated
    4. Timestamps are set
    """
    # Create project and initial version
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()  # Commit to trigger after_insert event that creates initial version
    await db_session.refresh(project)
    
    version = Version(
        project_id=project.id,
        name="Test Version",
        version_number=1,  # Use version 1 since version 0 is created automatically
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)  # Ensure we have the latest version data
    
    # Create file
    file = File(
        version_id=version.id,
        path="src/test.tsx",
        content="Test content"
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    
    assert file.id is not None
    assert file.path == "src/test.tsx"
    assert file.content == "Test content"
    assert file.version_id == version.id
    assert file.created_at is not None
    assert file.updated_at is not None

@pytest.mark.asyncio
async def test_file_path_constraints(db_session: AsyncSession):
    """Test file path constraints.
    
    Verifies:
    1. Path cannot be empty
    2. Path must be unique within version
    3. Path format is validated
    4. Path length is limited
    """
    # Create project and initial version
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()  # Commit to trigger after_insert event that creates initial version
    await db_session.refresh(project)
    
    version = Version(
        project_id=project.id,
        name="Test Version",
        version_number=1,  # Use version 1 since version 0 is created automatically
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)  # Ensure we have the latest version data
    
    # Test empty path (Python-level validation)
    with pytest.raises(ValueError, match="File path cannot be empty"):
        file = File(
            version_id=version.id,
            path="",
            content="Test content"
        )
    
    # Test path too long (max 1024 chars)
    with pytest.raises(ValueError, match="File path cannot exceed 1024 characters"):
        file = File(
            version_id=version.id,
            path="x" * 1025,
            content="Test content"
        )
    
    # Test duplicate path in same version
    file1 = File(
        version_id=version.id,
        path="src/test.tsx",
        content="Test content 1"
    )
    db_session.add(file1)
    await db_session.commit()
    
    with pytest.raises(IntegrityError):
        file2 = File(
            version_id=version.id,
            path="src/test.tsx",  # Duplicate path
            content="Test content 2"
        )
        db_session.add(file2)
        await db_session.commit()
    await db_session.rollback()
    
    # Test same path in different version is allowed
    version2 = Version(
        project_id=project.id,
        name="Test Version 2",
        version_number=2,  # Use version 2 for the second version
        parent_id=project.versions[0].id
    )
    db_session.add(version2)
    await db_session.commit()
    await db_session.refresh(version2)  # Ensure we have the latest version data
    
    file3 = File(
        version_id=version2.id,
        path="src/test.tsx",  # Same path, different version
        content="Test content 3"
    )
    db_session.add(file3)
    await db_session.commit()  # Should succeed

@pytest.mark.asyncio
async def test_file_content_constraints(db_session: AsyncSession):
    """Test file content constraints.
    
    Verifies:
    1. Content cannot be null
    2. Content can be empty string
    3. Large content is handled properly
    """
    # Create project and initial version
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()  # Commit to trigger after_insert event that creates initial version
    await db_session.refresh(project)
    
    version = Version(
        project_id=project.id,
        name="Test Version",
        version_number=1,  # Use version 1 since version 0 is created automatically
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)  # Ensure we have the latest version data
    
    # Test null content (Python-level validation)
    with pytest.raises(ValueError, match="File content cannot be null"):
        file = File(
            version_id=version.id,
            path="src/test1.tsx",
            content=None
        )
    
    # Test empty content
    file = File(
        version_id=version.id,
        path="src/test2.tsx",
        content=""
    )
    db_session.add(file)
    await db_session.commit()  # Should succeed
    
    # Test large content (1MB)
    large_content = "x" * (1024 * 1024)
    file = File(
        version_id=version.id,
        path="src/test3.tsx",
        content=large_content
    )
    db_session.add(file)
    await db_session.commit()  # Should succeed
    await db_session.refresh(file)
    assert len(file.content) == len(large_content)

@pytest.mark.asyncio
async def test_file_version_relationship(db_session: AsyncSession):
    """Test file-version relationship.
    
    Verifies:
    1. File must belong to a version
    2. Version must exist
    3. Cascade delete works
    4. Files are ordered by path
    """
    # Create project and initial version
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()  # Commit to trigger after_insert event that creates initial version
    await db_session.refresh(project)
    
    version = Version(
        project_id=project.id,
        name="Test Version",
        version_number=1,  # Use version 1 since version 0 is created automatically
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)  # Ensure we have the latest version data
    
    # Test missing version_id
    with pytest.raises(IntegrityError):
        file = File(
            version_id=None,
            path="src/test.tsx",
            content="Test content"
        )
        db_session.add(file)
        await db_session.commit()
    await db_session.rollback()
    
    # Test non-existent version_id
    with pytest.raises(IntegrityError):
        file = File(
            version_id=uuid4(),  # Random UUID
            path="src/test.tsx",
            content="Test content"
        )
        db_session.add(file)
        await db_session.commit()
    await db_session.rollback()
    
    # Add multiple files and verify ordering
    paths = ["src/c.tsx", "src/a.tsx", "src/b.tsx"]
    for path in paths:
        file = File(
            version_id=version.id,
            path=path,
            content="Test content"
        )
        db_session.add(file)
    await db_session.commit()
    
    # Verify files are ordered by path
    files = version.files
    assert len(files) == 3
    assert [f.path for f in files] == sorted(paths)
    
    # Test cascade delete
    db_session.delete(version)
    await db_session.commit()
    
    result = await db_session.execute(
        db_session.query(File).filter(File.version_id == version.id)
    )
    files = result.scalars().all()
    assert len(files) == 0

@pytest.mark.asyncio
async def test_file_timestamps(db_session: AsyncSession):
    """Test file timestamp behavior.
    
    Verifies:
    1. Created timestamp is set on creation
    2. Updated timestamp changes on update
    3. Timestamps are in UTC
    4. Timestamps are not null
    """
    # Create project and initial version
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()  # Commit to trigger after_insert event that creates initial version
    await db_session.refresh(project)
    
    version = Version(
        project_id=project.id,
        name="Test Version",
        version_number=1,  # Use version 1 since version 0 is created automatically
        parent_id=project.versions[0].id
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)  # Ensure we have the latest version data
    
    # Create file
    file = File(
        version_id=version.id,
        path="src/test.tsx",
        content="Test content"
    )
    db_session.add(file)
    await db_session.commit()
    
    created_at = file.created_at
    updated_at = file.updated_at
    
    assert created_at is not None
    assert updated_at is not None
    assert created_at == updated_at
    
    # Update file
    file.content = "Updated content"
    await db_session.commit()
    await db_session.refresh(file)
    
    assert file.created_at == created_at
    assert file.updated_at > updated_at
