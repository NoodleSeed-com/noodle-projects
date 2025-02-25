# System Patterns

## Microservice Best Practices Analysis (2025-02-25)

### Project Structure and Organization ✅

**Strengths:**
- Clear separation of concerns with distinct modules for models, schemas, routes, services, and CRUD operations
- Co-located tests with source code, improving discoverability and maintainability
- Proper use of package structure with __init__.py files for clean imports
- Modular design with focused components (e.g., splitting large version.py into a package)
- Consistent naming conventions throughout the codebase

**Improvement Areas:**
- The events.py file appears to be mostly empty with a comment about moving functionality to routes, which could be confusing

### API Design and Implementation ✅

**Strengths:**
- RESTful endpoint design with clear resource hierarchy
- Proper use of HTTP methods (GET, POST, PUT, DELETE)
- Consistent response models with Pydantic
- Comprehensive input validation
- Proper status code usage (201 for creation, 404 for not found, etc.)
- Dependency injection for database and services

**Improvement Areas:**
- Consider adding API versioning in the URL path for future compatibility

### Database Design and ORM Usage ✅

**Strengths:**
- Proper use of SQLAlchemy ORM with async support
- Well-designed models with appropriate relationships
- Use of UUID primary keys for better distribution
- Soft deletion through active flag
- Proper constraints (unique, check) at the database level
- Transaction management for data consistency

**Improvement Areas:**
- The event listener pattern for version validation could be simplified to avoid async issues

### Error Handling ✅

**Strengths:**
- Custom NoodleError class with error types
- Consistent error response format
- Proper mapping of error types to HTTP status codes
- Comprehensive exception handlers
- Validation at multiple levels (schema, model, database)

**Improvement Areas:**
- Consider adding more specific error types for better client feedback

### Testing Approach ✅

**Strengths:**
- Comprehensive test coverage (reported at 97%)
- Clear test organization with co-located tests
- Use of fixtures for test setup
- Transaction isolation for test independence
- Testing both success and error paths
- Mock services for external dependencies
- Clear test documentation with verification points

**Improvement Areas:**
- The SQLAlchemy event listener testing could be improved to avoid "coroutine was never awaited" warnings

### Async Implementation ⚠️

**Strengths:**
- Proper use of async/await throughout the codebase
- Async database operations with SQLAlchemy
- Async service calls to OpenRouter

**Improvement Areas:**
- The SQLAlchemy event listener issue with async functions needs to be addressed
- The comment in events.py suggests that functionality was moved to avoid async issues, which indicates a potential design problem

### Code Quality and Documentation ✅

**Strengths:**
- Comprehensive docstrings for functions and classes
- Type hints throughout the codebase
- Clear naming conventions
- Consistent code style
- Well-organized imports
- Detailed comments explaining complex logic

**Improvement Areas:**
- Some docstrings could be more detailed about error conditions

### Security Considerations ✅

**Strengths:**
- Input validation to prevent injection attacks
- Proper CORS configuration
- Environment-based configuration for sensitive data
- Proper error handling to avoid information leakage

**Improvement Areas:**
- Consider adding rate limiting for API endpoints
- Add more comprehensive authentication and authorization

### Recommendations

1. **Fix the SQLAlchemy event listener issue**: Implement the pattern described in systemPatterns.md using a synchronous event listener that schedules async tasks.

2. **Complete the remaining test fixes**: Address the test_inactive_version_operations test failure related to the async event listener issue.

3. **Consider API versioning**: Add version information to the API path for future compatibility.

4. **Enhance error types**: Add more specific error types for better client feedback.

5. **Add rate limiting**: Implement rate limiting for API endpoints to prevent abuse.

6. **Improve authentication**: Add comprehensive authentication and authorization mechanisms.

7. **Clean up events.py**: Either implement the event listeners properly or remove the file if it's no longer needed.

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

### FastAPI Testing Best Practices

1. Use a Separate Test Database
   - In-memory SQLite database for fast tests
   - Proper transaction isolation for test independence
   - Database setup and teardown for each test
   ```python
   # Use an in-memory SQLite database for testing
   TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
   engine = create_async_engine(TEST_DATABASE_URL, echo=True)
   TestingSessionLocal = sessionmaker(
       engine, class_=AsyncSession, expire_on_commit=False
   )
   ```

2. Dependency Injection
   - Override dependencies for testing
   - Use test-specific database session
   - Clear overrides after tests
   ```python
   @pytest.fixture
   def client(db_session):
       """Test client with test database session."""
       async def override_get_db():
           yield db_session
   
       app.dependency_overrides[get_db] = override_get_db
       with TestClient(app) as client:
           yield client
       app.dependency_overrides.clear()
   ```

3. Async Testing
   - Use pytest-asyncio for async tests
   - Add @pytest.mark.asyncio decorator to test functions
   - Properly await async operations
   ```python
   @pytest.mark.asyncio
   async def test_create_project(client, db_session):
       """Test creating a project."""
       response = client.post(
           "/api/projects/",
           json={
               "name": "Test Project",
               "description": "Test Description"
           }
       )
       assert response.status_code == 201
       project = response.json()
       assert project["name"] == "Test Project"
   ```

4. Transaction Isolation
   - Use transactions for test isolation
   - Rollback after each test
   - Avoid test interdependence
   ```python
   @pytest.fixture
   async def db_session(setup_database):
       """Create a test database session with transaction isolation."""
       connection = await engine.connect()
       transaction = await connection.begin()
       session = TestingSessionLocal(bind=connection)
       
       try:
           yield session
       finally:
           await session.close()
           await transaction.rollback()
           await connection.close()
   ```

### AsyncMock and SQLAlchemy Testing Patterns

1. AsyncMock Coroutine Handling
   - AsyncMock returns coroutines that must be awaited
   - Set side_effect = None to prevent coroutine behavior
   - Use MagicMock for query results
   ```python
   # Configure AsyncMock to not return coroutines
   mock_db_session.execute = AsyncMock()
   mock_db_session.execute.side_effect = None
   
   # Use MagicMock for query results
   result = MagicMock()
   result.scalar_one.return_value = True
   mock_db_session.execute.return_value = result
   ```

2. Sequence-Based Mocking for Multiple Queries
   - Use side_effect as a list for sequential calls
   - Create separate mock results for each query
   ```python
   # Create mock results for each query
   version_result = MagicMock()
   version_result.scalar_one_or_none.return_value = mock_version
   
   parent_result = MagicMock()
   parent_result.scalar_one_or_none.return_value = 0
   
   # Set up the execute mock to return the results in sequence
   mock_db_session.execute = AsyncMock()
   mock_db_session.execute.side_effect = [
       version_result,      # First call
       parent_result,       # Second call
   ]
   ```

3. Transaction Context Manager Mocking
   ```python
   # Mocking async context manager for transactions
   mock_db_session.begin.return_value.__aenter__.return_value = mock_db_session
   mock_db_session.begin.side_effect = None  # Prevent coroutine
   ```

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

### SQLAlchemy Event Listeners with Async Functions

1. Problem:
   - SQLAlchemy's event system doesn't natively support async functions
   - Using async functions as event listeners causes "coroutine was never awaited" warnings
   - Example of problematic code:
   ```python
   @event.listens_for(Project, 'after_insert')
   async def create_initial_version(mapper, connection, project):
       """Create version 0 with template files when a project is created."""
       # This async function is never properly awaited by SQLAlchemy's event system
       # ...
   ```

2. Solution Pattern:
   - Use a synchronous event listener that calls the async function using asyncio.create_task()
   - Example:
   ```python
   import asyncio
   from sqlalchemy.ext.asyncio import AsyncSession

   # Separate the async implementation
   async def async_create_initial_version(project_id, session):
       """Async implementation of initial version creation."""
       # Async implementation here
       pass

   # Create a synchronous event listener
   def create_initial_version_listener(mapper, connection, target):
       """Synchronous event listener that schedules the async function."""
       # Create a task to run the async function
       asyncio.create_task(
           async_create_initial_version(
               target.id, 
               AsyncSession(bind=connection)
           )
       )

   # Register the synchronous event listener
   event.listen(Project, 'after_insert', create_initial_version_listener)
   ```

3. Benefits:
   - Keeps the event listener synchronous, which is what SQLAlchemy expects
   - Allows async code to run in response to the event
   - Properly schedules the async function to run in the background
   - Avoids "coroutine was never awaited" warnings
   - Maintains proper async/await patterns

4. Testing Considerations:
   - In tests, you may need to mock asyncio.create_task to verify it was called
   - Consider adding a background task manager for error handling
   - Be cautious about test isolation when using background tasks
   - Consider using FastAPI's BackgroundTasks for better error handling

### Testing Async Code with pytest-asyncio

1. Setup:
   - Install pytest-asyncio: `pip install pytest-asyncio`
   - Mark tests with `@pytest.mark.asyncio`
   - Configure pytest.ini if needed:
   ```ini
   [pytest]
   asyncio_mode = auto
   ```

2. Async Test Structure:
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       # Arrange
       data = await setup_test_data()
       
       # Act
       result = await function_under_test(data)
       
       # Assert
       assert result == expected_result
   ```

3. Mocking Async Functions:
   ```python
   from unittest.mock import AsyncMock
   
   @pytest.mark.asyncio
   async def test_with_async_mock():
       # Create AsyncMock
       mock_service = AsyncMock()
       mock_service.get_data.return_value = {"key": "value"}
       
       # Use in test
       result = await function_that_uses_service(mock_service)
       
       # Verify
       mock_service.get_data.assert_called_once()
       assert result == expected_result
   ```

4. Handling Side Effects:
   ```python
   # For multiple return values
   mock_service.get_data.side_effect = [
       {"first": "response"},
       {"second": "response"}
   ]
   
   # For raising exceptions
   mock_service.get_data.side_effect = ValueError("Test error")
   
   # For custom async functions
   async def custom_side_effect(arg):
       return {"processed": arg}
       
   mock_service.get_data.side_effect = custom_side_effect
   ```

5. Common Pitfalls:
   - Forgetting to await async functions
   - Mixing sync and async code incorrectly
   - Not handling event loop properly
   - Improper transaction management in async tests

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

### Routes Testing Patterns

1. Test Client Setup:
   ```python
   @pytest.fixture
   def client(mock_db: Session):
       """Test client with mocked database."""
       def override_get_db():
           return mock_db

       app.dependency_overrides[get_db] = override_get_db
       with TestClient(app) as client:
           yield client
       app.dependency_overrides.clear()
   ```

2. Service Mocking:
   ```python
   @pytest.fixture
   def mock_openrouter():
       """Mock OpenRouter service for testing."""
       async def mock_service():
           mock = MagicMock()
           mock.get_file_changes.return_value = []
           return mock
       
       app.dependency_overrides[get_openrouter] = mock_service
       yield mock_service
       app.dependency_overrides.clear()
   ```

3. Test Categories:
   - Success Cases: Test normal operation paths
   - Error Cases: Test validation and error handling
   - Edge Cases: Test boundary conditions

4. JSON Request Patterns:
   ```python
   # Always include commas between properties
   client.post("/api/projects/", json={
       "name": "Test Project",
       "description": "Test Description"
   })
   ```

5. Response Validation Patterns:
   ```python
   # Status code validation
   assert response.status_code == 201
   
   # Response structure validation
   data = response.json()
   assert "id" in data
   assert data["name"] == "Test Project"
   
   # Error response validation
   assert response.status_code == 400
   error = response.json()
   assert "detail" in error
   assert isinstance(error["detail"], str)
   ```

## SQLAlchemy Patterns

### SQLAlchemy Session Management

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

### Transaction Management

1. Transaction Boundaries:
   - Define clear transaction boundaries
   - Use context managers for transactions
   - Handle rollbacks on errors
   - Example:
   ```python
   async with db.begin():
       # Operations within transaction
       db.add(model)
       # Automatically commits or rolls back
   ```

2. Nested Transactions:
   - Use savepoints for nested operations
   - Roll back to savepoint on error
   - Maintain outer transaction
   - Example:
   ```python
   async with db.begin_nested():
       # Operations that might fail
       db.add(model)
       # Rolls back to savepoint on error
   ```

3. Error Handling:
   - Catch specific exceptions
   - Roll back transaction on error
   - Provide clear error messages
   - Example:
   ```python
   try:
       async with db.begin():
           db.add(model)
   except IntegrityError:
       # Handle constraint violation
   ```

## Version Management Patterns

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
