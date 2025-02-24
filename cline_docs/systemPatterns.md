# System Patterns

## Test Organization Patterns

### Co-located Tests Pattern
Tests are organized close to the code they test, following a consistent structure:

```
api/app/
├── models/
│   ├── __init__.py
│   ├── model.py
│   └── tests/              # Model tests
│       ├── conftest.py     # Model-specific fixtures
│       └── test_model.py
├── routes/
│   ├── __init__.py
│   ├── route.py
│   └── tests/              # Route tests
│       ├── conftest.py     # Route-specific fixtures
│       └── test_route.py
└── services/
    ├── __init__.py
    ├── service.py
    └── tests/              # Service tests
        ├── conftest.py     # Service-specific fixtures
        └── test_service.py
```

Benefits:
1. Improved Discoverability:
   - Tests are easy to find
   - Clear relationship to source code
   - Natural navigation

2. Clear Ownership:
   - Tests belong to module
   - Module owners maintain tests
   - Focused responsibility

3. Better Maintainability:
   - Tests move with code
   - Easier refactoring
   - Reduced coupling

4. Direct Context:
   - Tests have access to internals
   - Easier mocking
   - Better isolation

### Test Database Setup Patterns

1. Module-Level Database:
   ```python
   @pytest.fixture(scope="module")
   def test_db(test_engine):
       Base.metadata.drop_all(bind=test_engine)
       Base.metadata.create_all(bind=test_engine)
       TestingSessionLocal = sessionmaker(...)
       db = TestingSessionLocal()
       yield db
       db.close()
       Base.metadata.drop_all(bind=test_engine)
   ```

   Considerations:
   - Handle foreign key constraints
   - Manage transaction isolation
   - Clean state between tests
   - Proper cleanup on failure

2. Test-Level Transactions:
   ```python
   @pytest.fixture
   def db_session(test_db):
       test_db.begin_nested()  # Create savepoint
       yield test_db
       test_db.rollback()      # Rollback to savepoint
       test_db.expire_all()
   ```

   Benefits:
   - Isolated test state
   - Automatic cleanup
   - No cross-test pollution
   - Fast execution

### Test Coverage Patterns

1. Coverage Goals:
   - 100% for models
   - 100% for critical paths
   - 80% minimum overall
   - Focus on business logic

2. Coverage Strategy:
   - Start with model tests
   - Add route tests
   - Cover service layer
   - Integration tests last

3. Test Categories:
   - Unit Tests: Direct module testing
   - Integration Tests: Cross-module flows
   - End-to-End: Full system tests
   - Performance Tests: Load testing

### Test Naming Patterns

1. File Names:
   - test_*.py for test files
   - conftest.py for fixtures
   - __init__.py for organization

2. Test Names:
   - test_*() for test functions
   - Descriptive names
   - Action_Result pattern
   - Include_Scenario pattern

3. Fixture Names:
   - Descriptive purpose
   - Module prefix when needed
   - Indicate scope if relevant
   - Document dependencies

### Test Documentation Patterns

1. Test Docstrings:
   ```python
   def test_version_creation(db_session):
       """Test version creation.
       
       Verifies:
       1. Version attributes set correctly
       2. Relationships established
       3. Constraints enforced
       4. Events triggered
       """
   ```

2. Fixture Documentation:
   ```python
   @pytest.fixture
   def test_db():
       """Provide clean database for each module.
       
       Handles:
       - Table creation
       - Data cleanup
       - Transaction isolation
       - Resource cleanup
       """
   ```

### Test Fixture Patterns

1. Scope Hierarchy:
   - Session: Entire test run
   - Module: Single test file
   - Class: Test class
   - Function: Single test

2. Dependency Chain:
   ```python
   @pytest.fixture(scope="session")
   def test_engine():
       """Database engine for tests."""
       
   @pytest.fixture(scope="module")
   def test_db(test_engine):
       """Module database from engine."""
       
   @pytest.fixture
   def db_session(test_db):
       """Test transaction from database."""
   ```

3. Resource Management:
   - Proper cleanup
   - Error handling
   - Resource sharing
   - State isolation

### Test Isolation Patterns

1. Database Isolation:
   - Transaction rollback
   - Separate test database
   - Clean state per test
   - No shared state

2. Service Isolation:
   - Mock external services
   - Stub responses
   - Control timing
   - Error simulation

3. Environment Isolation:
   - Test-specific config
   - Controlled randomness
   - Time manipulation
   - Path isolation

### Error Handling Patterns

1. Expected Errors:
   ```python
   with pytest.raises(ValueError) as exc:
       # Test code that should raise error
   assert str(exc.value) == "Expected message"
   ```

2. Database Errors:
   ```python
   with pytest.raises(IntegrityError):
       # Test constraint violation
   ```

3. Async Errors:
   ```python
   with pytest.raises(AsyncError):
       await async_operation()
   ```

### Test Data Patterns

1. Factory Functions:
   ```python
   def create_test_version(db, **kwargs):
       """Create test version with defaults."""
       defaults = {
           "name": "Test Version",
           "number": 1
       }
       defaults.update(kwargs)
       return Version(**defaults)
   ```

2. Fixture Data:
   ```python
   @pytest.fixture
   def sample_data():
       return {
           "name": "Test",
           "value": 123
       }
   ```

3. Test Constants:
   ```python
   TEST_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
   TEST_NAME = "Test Project"
   ```

## Lessons Learned

1. Database Setup:
   - Handle constraints properly
   - Use transactions for isolation
   - Clean up resources
   - Maintain test independence

2. Test Organization:
   - Co-locate with source
   - Clear ownership
   - Focused scope
   - Easy navigation

3. Coverage Strategy:
   - Start with models
   - Add routes
   - Cover services
   - End-to-end last

4. Documentation:
   - Clear purpose
   - Verification points
   - Setup requirements
   - Expected results

### SQLAlchemy Testing Patterns

1. Session Management:
   ```python
   # Create and commit
   db_session.add(project)
   db_session.commit()
   db_session.refresh(project)  # Reload to get generated values
   
   # Verify state after commit
   assert len(project.versions) == 1
   initial_version = project.versions[0]
   ```

2. Unique Constraint Handling:
   - Check table constraints before creating records
   - Use explicit version numbers to avoid conflicts
   - Handle unique constraint violations in tests
   - Example:
   ```python
   # Initial version (0) is auto-created
   version = Version(
       project_id=project.id,
       version_number=1,  # Use explicit next number
       name="Test Version"
   )
   ```

3. Event Listener Testing:
   - Commit to trigger after_insert events
   - Refresh to load generated relationships
   - Verify event results after commit
   - Example:
   ```python
   # Create project triggers version creation
   project = Project(name="Test")
   db_session.add(project)
   db_session.commit()
   db_session.refresh(project)
   
   # Verify event created version
   assert len(project.versions) == 1
   assert project.versions[0].version_number == 0
   ```

4. Relationship Testing:
   - Test cascading effects (e.g., soft delete)
   - Verify bidirectional relationships
   - Check constraint enforcement
   - Example:
   ```python
   # Test soft delete cascades
   project.active = False
   db_session.commit()
   db_session.refresh(project)
   
   for version in project.versions:
       assert version.active is False
   ```

5. Common Pitfalls:
   - Using flush() when commit() is needed for events
   - Not refreshing after commits
   - Duplicate version numbers
   - Missing relationship loads

### Version Management Patterns

1. Version Relationships:
   ```python
   class Version(Base):
       # Self-referential relationship for version hierarchy
       parent_id = mapped_column(ForeignKey("versions.id"))
       # Each version belongs to a project
       project_id = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
   ```

2. Version Numbering:
   - Version 0 reserved for initial version
   - Auto-create initial version on project creation
   - Sequential numbering for clarity
   - Unique constraint on (project_id, version_number)
   ```python
   @event.listens_for(Project, 'after_insert')
   def create_initial_version(mapper, connection, project):
       """Create version 0 when project is created."""
       version = Version(
           project_id=project.id,
           version_number=0,
           name="Initial Version"
       )
   ```

3. Version Deletion Patterns:
   - Consider referential integrity
   - Parent versions referenced by children
   - Two approaches:
     a. Soft Delete (Preferred):
        - Keep version records
        - Mark as inactive
        - Maintain history
        - Example:
        ```python
        # Soft delete cascades to versions
        project.active = False
        db_session.commit()
        ```
     b. Hard Delete:
        - Requires careful ordering
        - Delete children first
        - Complex with deep hierarchies
        - Can lose history

4. Version Testing Patterns:
   - Test initial version creation
   - Verify numbering sequence
   - Check relationship constraints
   - Example:
   ```python
   def test_version_creation(db_session):
       project = Project(name="Test")
       db_session.add(project)
       db_session.commit()  # Triggers initial version
       
       # Add new version
       version = Version(
           project_id=project.id,
           version_number=1,  # Next after initial 0
           parent_id=project.versions[0].id
       )
       db_session.add(version)
       db_session.commit()
   ```

5. Version Management Lessons:
   - Always commit() to trigger version events
   - Use explicit version numbers
   - Consider relationship impacts
   - Prefer soft delete for history
   - Test deletion scenarios thoroughly
   - Document version patterns

6. Version Validation Patterns:
   - Python-level validation in __init__:
     * Empty paths
     * Null content
     * Project active state
     * Path length limits
   - Database-level constraints:
     * Unique version numbers per project
     * Foreign key relationships
     * Cascade delete behavior

7. Version Testing Patterns:
   - Test both Python and DB validations:
     ```python
     # Python-level validation
     with pytest.raises(ValueError, match="File path cannot be empty"):
         file = File(path="", content="test")
     
     # Database-level validation
     with pytest.raises(IntegrityError):
         version = Version(version_number=0)  # Duplicate number
         db_session.add(version)
         db_session.commit()
     ```
   - Use commit() to trigger events:
     ```python
     # Create project (triggers initial version)
     project = Project(name="Test")
     db_session.add(project)
     db_session.commit()  # Not flush()
     db_session.refresh(project)
     ```
   - Set explicit version numbers:
     ```python
     # Get next available number
     next_number = max(v.version_number for v in project.versions) + 1
     version = Version(version_number=next_number)
     ```
   - Test soft delete cascades:
     ```python
     # Soft delete cascades to versions
     project.active = False
     db_session.commit()
     db_session.refresh(project)
     
     for version in project.versions:
         assert version.active is False
     ```
