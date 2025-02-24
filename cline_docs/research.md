# Research Findings

## FastAPI Best Practices

### Pydantic v2 Models
Research via Perplexity AI revealed current best practices:

1. Model Configuration
   - Use `model_config` with `ConfigDict` instead of `Config` class
   - Enable `from_attributes=True` for ORM compatibility
   - Add JSON schema examples for better documentation

2. Field Validation
   - Use `Field()` for validation and metadata
   - Provide descriptions for OpenAPI documentation
   - Set appropriate default values

3. Model Structure
   - Create base models for shared attributes
   - Use inheritance for request/response models
   - Implement proper validation rules

Example Implementation:
```python
class ProjectBase(BaseModel):
    """Base model for project data"""
    name: str = Field(..., description="The name of the project")
    description: str = Field("", description="Project description")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "My Project",
                "description": "A sample project description"
            }
        }
    )
```

## Database Design Decisions

### Version Management
Research findings on version control patterns:

1. Version Numbering
   - Sequential within project scope
   - Tracked at project level
   - No gaps in numbering
   - Parent-child relationships

2. Storage Strategy
   - Files linked to specific versions
   - No direct file manipulation
   - Path uniqueness per version
   - Content stored as text

### Indexing Strategy
Based on common query patterns:

1. Primary Lookups
   - Project by ID
   - Version by project and number
   - Files by version and path

2. Performance Optimization
   - Composite index on version lookup
   - Index on foreign keys
   - Unique constraints as indexes

## API Design Patterns

### RESTful Best Practices
Research on modern API design:

1. Resource Naming
   - Noun-based endpoints
   - Clear hierarchy
   - Consistent patterns
   - Version in path

2. Status Codes
   - 200: Successful operations
   - 201: Resource creation
   - 404: Not found
   - 400: Validation errors

3. Query Parameters
   - Pagination with skip/limit
   - Optional filtering
   - Default values
   - Parameter validation

## Implementation Insights

### Error Handling
Best practices for API errors:

1. Exception Types
   - HTTP exceptions
   - Database errors
   - Validation errors
   - Custom errors

2. Response Format
   - Consistent structure
   - Clear messages
   - Proper status codes
   - Additional context

## OpenRouter Integration with Gemini

### Response Format Validation
Research findings from Gemini 2.0 Flash testing:

1. Response Structure
   - Responses consistently wrapped in `<noodle_response>` tags
   - Valid JSON structure within tags
   - Proper escaping of code content
   ```json
   <noodle_response>
   {"changes": [{
     "operation": "create",
     "path": "src/components/Button.tsx",
     "content": "import React from 'react';\n..."
   }]}
   </noodle_response>
   ```

2. Code Generation Capabilities
   - Accurate TypeScript type definitions
   - Modern React patterns (functional components, hooks)
   - Styled-components implementation
   - Accessibility considerations
   - Proper component exports

3. Model Selection
   - google/gemini-2.0-flash-001 suitable for code generation
   - Fast response times
   - Consistent formatting
   - Follows provided templates

4. Integration Patterns
   - Environment-based configuration
   - Proper error handling
   - Response validation
   - Content parsing
   - Testing considerations

### Key Learnings
1. Response Validation
   - Always verify `<noodle_response>` tags presence
   - Validate JSON structure
   - Check required fields (operation, path, content)
   - Verify operation values (create, update, delete)

2. Error Handling
   - Handle missing API keys gracefully
   - Validate response format
   - Parse JSON safely
   - Provide clear error messages

## Transaction Management Issues

### Concurrent State Changes
Investigation of test failure in `test_concurrent_state_changes`:

1. Error Analysis
   ```
   sqlalchemy.exc.IllegalStateChangeError: Method 'commit()' can't be called here; method 'commit()' is already in progress
   ```
   - Multiple transactions attempting to commit simultaneously
   - SQLAlchemy state management conflict
   - Potential race condition in concurrent operations

2. Root Cause
   - Concurrent state updates not properly synchronized
   - Transaction boundaries not clearly defined
   - Possible nested transaction issue

3. Recommended Solutions
   - Implement proper transaction isolation
   - Use SQLAlchemy session management best practices
   - Add explicit transaction boundaries
   - Consider using savepoints for nested operations

## Routes Test Coverage Analysis (2024-02-24)

### Test Coverage Assessment
Research findings from routes test coverage analysis:

1. Coverage Metrics
   - app/routes/__init__.py: 100% coverage (6/6 statements)
   - app/routes/projects.py: 40% coverage (19/37 statements missed, 8 branches)
   - app/routes/versions.py: 25% coverage (33/49 statements missed, 14 branches)
   - Overall routes coverage: ~40%

2. Test Execution Issues
   - Missing `mock_db` fixture in routes tests conftest.py
   - Implementation mismatch: `AttributeError: 'VersionCRUD' object has no attribute 'create_initial_version'`
   - JSON syntax errors in test files (missing commas between properties)

3. Coverage Gaps
   - Error paths in both routes files not covered
   - Exception handling in create_version mostly untested
   - Validation logic partially tested

### Test Fixture Patterns
Research on effective test fixture patterns for FastAPI routes:

1. Mock Database Setup
   ```python
   @pytest.fixture(scope="module")
   def mock_db(mock_project, mock_version):
       """Mock database session for testing."""
       mock = AsyncMock()
       
       # Configure async methods
       mock.commit = AsyncMock()
       mock.rollback = AsyncMock()
       
       # Configure mock results
       project_result = MagicMock()
       project_result.scalar_one_or_none = lambda: mock_project
       
       version_result = MagicMock()
       version_result.scalar_one_or_none = lambda: mock_version
       
       # Configure execute to return appropriate result
       mock.execute = AsyncMock(return_value=version_result)
       
       return mock
   ```

2. FastAPI Test Client Setup
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

3. Service Mocking
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

### Common Test Issues
Research findings on common issues in FastAPI route testing:

1. JSON Syntax Errors
   - Missing commas between properties
   - Incorrect nesting of objects
   - Trailing commas in arrays
   - Example:
     ```python
     # Incorrect
     client.post("/api/projects/", json={
         "name": "Test Project"  # Missing comma
         "description": "Test Description"
     })
     
     # Correct
     client.post("/api/projects/", json={
         "name": "Test Project",
         "description": "Test Description"
     })
     ```

2. Dependency Injection Issues
   - Missing or incorrect dependency overrides
   - Forgetting to clear overrides after tests
   - Not mocking all required dependencies
   - Example:
     ```python
     # Before test
     app.dependency_overrides[get_db] = lambda: mock_db
     app.dependency_overrides[get_openrouter] = lambda: mock_openrouter
     
     # After test
     app.dependency_overrides.clear()  # Clear ALL overrides
     ```

3. Async/Sync Mismatches
   - Using sync functions with async dependencies
   - Not awaiting async operations
   - Mixing async and sync code
   - Example:
     ```python
     # Incorrect
     result = mock_db.execute(query)  # Should be awaited
     
     # Correct
     result = await mock_db.execute(query)
     ```

4. Implementation Mismatches
   - Methods called in routes but not implemented in services
   - Different parameter expectations
   - Return type mismatches
   - Example:
     ```python
     # Route calls create_initial_version
     await versions.create_initial_version(db, db_project.id)
     
     # But VersionCRUD doesn't implement it
     class VersionCRUD:
         # Missing create_initial_version method
         pass
     ```

### Recommendations for Improving Test Coverage
Based on research findings:

1. Fix Implementation Issues
   - Implement missing `create_initial_version` method in VersionCRUD class
   - Fix JSON syntax errors in test files
   - Ensure all dependencies are properly mocked

2. Add Tests for Error Paths
   - Test validation errors
   - Test not found scenarios
   - Test permission errors
   - Test integrity constraint violations

3. Test Exception Handling
   - Test each exception type in create_version
   - Verify error responses
   - Check transaction rollback
   - Validate error messages

4. Improve Test Organization
   - Group tests by endpoint
   - Add test categories (success, error, edge cases)
   - Document test coverage goals
   - Track coverage improvements

## Future Research Topics

1. Batch Operations
   - Efficient processing
   - Transaction management
   - Error handling
   - Progress tracking

2. Advanced Querying
   - Search implementation
   - Filter optimization
   - Sort mechanisms
   - Query validation

3. Performance Monitoring
   - Metrics collection
   - Query analysis
   - Resource usage
   - Optimization opportunities

## Service Integration Testing

### OpenRouter Service Testing Issues
Research findings from test implementation:

1. Mocking Challenges
   - Direct service imports make mocking difficult
   - Testing mode returns empty list by default
   - Mock not being called due to import structure

2. Current Implementation
   ```python
   # projects.py
   from app.services.openrouter import openrouter  # Direct import

   # Test
   @pytest.fixture
   def mock_openrouter():
       with patch("app.services.openrouter.openrouter") as mock_service:
           mock_service.get_file_changes.return_value = [...]
   ```

3. Recommended Patterns
   - Use dependency injection for services
   - Avoid direct imports of service instances
   - Make test mode behavior configurable
   - Document mocking requirements

4. Solution Implementation
   - Move service dependency to module level:
     ```python
     # services/openrouter.py
     openrouter = OpenRouterService()
     
     def get_openrouter():
         """Dependency to get OpenRouter service."""
         return openrouter
     ```
   - Use dependency in routes:
     ```python
     # projects.py
     from app.services.openrouter import get_openrouter
     
     @router.post("/versions")
     def create_version(
         openrouter_service = Depends(get_openrouter)
     ):
         changes = openrouter_service.get_file_changes(...)
     ```
   - Override in tests:
     ```python
     # conftest.py
     app.dependency_overrides[get_openrouter] = lambda: mock_openrouter
     ```
   - Verify service calls:
     ```python
     # Instead of assert_called_once_with():
     mock_openrouter.get_file_changes.assert_called_once()
     call_args = mock_openrouter.get_file_changes.call_args[1]
     assert call_args["project_context"] == expected_context
     ```

5. Key Learnings
   - Keep service dependencies centralized in their modules
   - Use consistent import paths for dependencies
   - Clear overrides after tests
   - When testing service calls with complex parameters:
     * Use assert_called_once() to verify the call happened
     * Check individual arguments using call_args[1] for kwargs
     * This is more flexible than assert_called_once_with()

### Error Handling Improvements
Research findings from edge case testing:

1. Service Layer Error Handling
   - Validate inputs before processing
   - Raise appropriate exceptions (ValueError, IntegrityError)
   - Maintain consistent error messages
   - Document error conditions

2. Error Propagation Patterns
   - Catch errors at appropriate layer
   - Convert to HTTP status codes:
     * ValueError -> 400 Bad Request
     * IntegrityError -> 409 Conflict
     * OperationalError -> 503 Service Unavailable
   - Maintain transaction integrity
   - Roll back on failure

3. Testing Strategy
   - Test validation failures
   - Verify error propagation
   - Check transaction rollback
   - Validate error responses
   - Mock service errors

4. Mock Integration
   - Use FastAPI dependency overrides
   - Mock service responses
   - Simulate error conditions
   - Verify error handling flow

5. Key Findings
   - Avoid nested try-except blocks
   - Use single error handling layer
   - Maintain clear error mapping
   - Document error scenarios
   - Test both success and failure paths

### Test Organization Patterns
Research findings from test refactoring:

1. Test Directory Structure
   - Unit tests in api/tests/unit_tests/
     * Tests using mocks (especially mock_openrouter)
     * Tests with controlled dependencies
     * Tests verifying specific behaviors
   - Integration tests in api/tests/integration_tests/
     * Tests using real dependencies
     * End-to-end behavior verification
     * Component interaction tests

2. Concurrent Testing Best Practices
   - Start with low concurrency (3 concurrent requests)
   - Increase concurrency after stability verified
   - Use max_workers parameter to control thread pool
   - Add transaction completion checks:
     ```python
     # Wait for transactions to complete
     for response in responses:
         if response.status_code == 200:
             client.get(f"/api/projects/{project_id}")
     ```

3. Database Fixture Usage
   - mock_db for unit tests
     * Controlled environment
     * Predictable behavior
     * Fast execution
   - test_db for integration tests
     * Real database operations
     * Transaction management
     * State verification

4. Common Issues Found
   - Response validation errors (missing required fields)
   - Transaction state conflicts
   - JSON syntax errors in test data
   - Concurrent operation race conditions

5. Key Learnings
   - Keep mock-dependent tests in unit_tests/
   - Use clear test categorization
   - Start with low concurrency
   - Verify transaction completion
   - Include proper state checks

## SQLAlchemy Async Testing Patterns (2024-02-23)

### Mock Response Type Issues (Updated 2024-02-23)
Investigation of test failures in edge case tests revealed critical mocking patterns:

1. Problem Analysis
   - Error: `AttributeError: 'Project' object has no attribute 'files'`
   - Root cause: Mock returning Project instead of Version for version queries
   - Complex query patterns with joinedload relationships causing type mismatches
   - String-based query inspection proving unreliable

2. Query Patterns Requiring Different Return Types
   ```python
   # Project queries:
   select(Project).options(joinedload(Project.versions))
   select(Project).filter(Project.active == True)
   select(Project.active)
   update(Project)

   # Version queries:
   select(Version).options(joinedload(Version.files))
   select(Version.version_number)
   select(Version.id, Version.version_number, Version.name)
   ```

3. Attempted Solutions
   a. Parameter-based mocking:
      ```python
      # Issue: Too simplistic, doesn't handle complex queries
      mock.execute = AsyncMock(
          return_value=version_result if param == "versions" else project_result
      )
      ```

   b. Query string inspection:
      ```python
      # Issue: Brittle, depends on string representation
      if "Version" in str(query):
          return version_result
      ```

   c. Query structure inspection:
      ```python
      # Issue: Complex to maintain, tight coupling to SQLAlchemy internals
      if isinstance(query, Select) and query.froms[0].name == 'versions':
          return version_result
      ```

4. Key Learnings
   - String-based query inspection is unreliable
   - Need better pattern for handling different query types
   - Consider refactoring to simpler query patterns
   - May need separate test classes for different query types
   - Integration tests might be more suitable for complex queries

5. Next Steps
   - Research SQLAlchemy test patterns for complex queries
   - Consider mock-alchemy library for better query mocking
   - Evaluate test structure reorganization
   - Document query patterns and expected returns

### Mock Response Type Issues
Investigation of test failures in edge case tests revealed critical mocking patterns:

1. Problem Analysis
   - Error: `AttributeError: 'Project' object has no attribute 'parent_id'`
   - Error: `AttributeError: 'Version' object has no attribute 'active'`
   - Root cause: Mock returning wrong model types for different queries
   - Parameterized fixture causing type confusion

2. Query Result Patterns
   ```python
   # Different return types needed:
   crud.get(db, project_id) -> Project  # Should return Project instance
   crud.get_version(db, project_id, version) -> VersionResponse  # Should return VersionResponse
   ```

3. Mock Implementation Challenges
   - Single mock needs to handle multiple query types
   - Each query type expects different return model
   - Query inspection needed to determine return type
   - Async/sync method mixing causing issues

4. Bad Pattern: Simple Parameterized Returns
   ```python
   # DON'T: Returns wrong types for different queries
   @pytest.fixture(params=["project", "version"])
   def mock_db(request):
       result = MagicMock()
       if request.param == "project":
           result.scalar_one_or_none = lambda: mock_project
       else:
           result.scalar_one_or_none = lambda: mock_version
       return result
   ```

5. Good Pattern: Query-Based Returns
   ```python
   # DO: Return based on query type
   async def mock_execute(query):
       if "Project.active" in str(query):
           return MagicMock(scalar_one=lambda: True)
       if "Version" in str(query):
           return MagicMock(
               unique=lambda: self,
               scalar_one_or_none=lambda: mock_version
           )
       # Default Project queries
       return MagicMock(
           scalar_one_or_none=lambda: mock_project
       )
   ```

6. Key Learnings
   - Mock returns must match model types exactly
   - Query inspection better than parameterization
   - Consider separate mocks for different query types
   - Document expected return types clearly
   - Test mock behavior independently

### Event Loop Management Issues
Investigation of test failures revealed critical async testing patterns:

1. Event Loop Conflicts
   - Different requirements for asyncio vs trio
   - Loop sharing between tests causing issues
   - Need for proper cleanup between tests
   - Error: "Task got Future attached to a different loop"

2. Transaction Management Challenges
   - Concurrent operation conflicts with asyncpg
   - Error: "cannot perform operation: another operation is in progress"
   - Need for proper transaction isolation
   - Connection state management critical

3. Model Access Patterns
   - Hybrid properties causing async issues
   - Relationship loading strategy impacts
   - Success with eager loading via selectin
   - Property calculation from loaded data

4. Recommended Solutions
   - Use selectin loading for relationships
   - Calculate properties from loaded data
   - Proper transaction isolation
   - Clear connection state between tests

Example Implementation:
```python
class Project(Base):
    versions = relationship(
        "Version",
        lazy="selectin",  # Eager loading
        cascade="all, delete-orphan"
    )

    @property
    def latest_version_number(self) -> int:
        """Calculate from loaded versions."""
        return max((v.version_number for v in self.versions), default=0)
```

Key Findings:
- Avoid async operations in property getters
- Use eager loading for related data
- Maintain clear transaction boundaries
- Handle connection cleanup properly
