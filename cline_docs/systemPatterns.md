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
