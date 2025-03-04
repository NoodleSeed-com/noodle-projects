# Noodle Projects Testing Guide

This document outlines the testing structure and best practices for the Noodle Projects API.

## Testing Philosophy

We use a layered testing approach with a clear separation:

1. **Unit Tests**: Test individual functions and classes in isolation, using mock objects
2. **Integration Tests**: Test components working together with a real PostgreSQL database
3. **API Tests**: Test HTTP endpoints and full request/response cycles

**Important**: We no longer use SQLite for testing. All integration tests use PostgreSQL with transaction isolation.

## Testing Structure

Tests are organized by type:

```
api/tests/
├── fixtures/           # Shared test fixtures
│   ├── db.py           # Database fixtures (mocks and PostgreSQL)
│   └── ...
├── unit_tests/         # Unit tests with mock objects
├── integration_tests/  # Integration tests with PostgreSQL
└── conftest.py         # Root test configuration
```

## Running Tests

### All Tests

```bash
pytest
```

### Specific Test Types

```bash
# Run unit tests only
pytest -m "unit"

# Run integration tests only
pytest -m "integration"

# Run tests for a specific module
pytest api/tests/unit/test_file.py
```

### With Coverage

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

## Test Fixtures

We use centralized fixtures in the `api/tests/fixtures/` directory:

- `db.py`: Database fixtures with two categories:
  - Mock database sessions for unit tests
  - Real PostgreSQL connections with transaction isolation for integration tests
- `env.py`: Environment variable management
- `fs.py`: File system operations
- `client.py`: API client fixtures
- `mocks.py`: Mock implementations of services
- `auth.py`: Authentication fixtures
- `validators.py`: Response validation utilities

Fixtures are automatically imported in `conftest.py` and available to all tests.

## Database Configuration

All tests requiring a database use PostgreSQL exclusively:

```python
# For unit tests
mock_db = AsyncMock()  # From unittest.mock, completely isolated

# For integration tests - real PostgreSQL with transaction isolation
@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine):
    """Real database session with transaction isolation."""
    session_maker = async_sessionmaker(bind=test_engine)
    async with session_maker() as session:
        await session.begin()  # Start transaction
        yield session
        await session.rollback()  # Roll back changes after test
```

Integration tests connect to PostgreSQL using these environment variables:

```
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
TEST_DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
TEST_MODE=true
```

## Best Practices

### General Guidelines

1. **Test Isolation**: Each test should run independently and not affect other tests
2. **Descriptive Names**: Test names should describe what is being tested
3. **Arrange-Act-Assert**: Follow the AAA pattern in tests

### Unit Tests

1. Use AsyncMock for database and external dependencies
2. Always use explicit mocking with clear return values
3. Test edge cases and error conditions
4. Use pytest.mark.unit and pytest.mark.asyncio decorators

Example unit test with mock database:

```python
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
        active=True
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
    assert result is mock_project
    assert result.name == "Test Project"
    
    # Verify db interactions
    mock_db.execute.assert_called_once()
```

### Integration Tests

1. Use `db_session` fixture for database operations with PostgreSQL
2. All operations in a test are wrapped in a transaction that is rolled back at the end
3. Test database constraints and ORM relationship handling
4. Use pytest.mark.integration and pytest.mark.asyncio decorators

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_project_and_verify_in_db(db_session):
    """Test creating and retrieving a project from the database."""
    # Arrange
    project_data = ProjectCreate(
        name="Integration Test Project",
        description="Test Description"
    )
    
    # Act - Create a project
    new_project = await ProjectCRUD.create(db=db_session, project=project_data)
    
    # Verify created project has expected properties
    assert new_project.id is not None
    assert new_project.name == "Integration Test Project"
    assert new_project.active is True
    
    # Act - Get the project from the database
    retrieved = await ProjectCRUD.get(db=db_session, project_id=new_project.id)
    
    # Assert - Verify it matches what we created
    assert retrieved is not None
    assert retrieved.id == new_project.id
    assert retrieved.name == "Integration Test Project"
    
    # No cleanup needed - transaction is rolled back automatically
```

### API Tests

1. Use `client` or `async_client` fixtures
2. Validate response status codes and content
3. Use schema validation with `validate_response`

```python
@pytest.mark.integration
async def test_get_project_endpoint(async_client, db_session, create_payload, validate_response):
    # Arrange
    payload = create_payload("project")
    project = await create_project(db_session, ProjectCreate(**payload))
    
    # Act
    response = await async_client.get(f"/api/projects/{project.id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    validate_response(data, ProjectResponse)
    assert data["name"] == payload["name"]
```

## Environment Variables

Create a `.env` file in the `api/tests/` directory based on `.env.example` to customize test behavior.

For tests requiring external services like Supabase:

```python
@pytest.mark.requires_supabase
@pytest.mark.integration
async def test_with_supabase(db_session):
    # This test will be skipped if SUPABASE_URL and SUPABASE_KEY are not set
    ...
```

## Adding New Tests

1. Choose the appropriate test type:
   - **Unit tests**: For individual functions with mocked dependencies
   - **Integration tests**: For components with real database operations

2. Use the correct fixtures based on test type:
   - Unit tests: Create your own AsyncMock objects or use the mock_db_session fixture
   - Integration tests: Use the db_session fixture for database operations

3. Follow these naming conventions:
   - Test files: `test_<module>_<feature>.py`
   - Test functions: `test_<function>_<scenario>()`

4. Always add appropriate markers:
   - `@pytest.mark.unit` for unit tests
   - `@pytest.mark.integration` for integration tests
   - `@pytest.mark.asyncio` for async functions

5. Debug your tests with:
   ```bash
   pytest -xvs path/to/your/test.py
   ```

## Continuous Integration

Tests run automatically in CI pipeline with PostgreSQL. Make sure your tests pass locally before pushing:

```bash
# Run both unit and integration tests
pytest

# Run only unit tests
pytest -m "unit"
```