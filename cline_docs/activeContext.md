# Active Context

## Current State (Updated 2024-02-23 22:49 PST)
Currently addressing test failures in edge case tests, specifically focusing on SQLAlchemy mocking issues in test_partial_version_creation_rollback.

## Test Failures (In Priority Order)
1. SQLAlchemy Mock Response Types (Current Focus)
   - test_partial_version_creation_rollback failing
   - Error: `AttributeError: 'Project' object has no attribute 'files'`
   - Root cause: Mock returning Project instead of ProjectVersion for version queries
   - Attempted solutions:
     * Parameter-based mocking (too simplistic)
     * Query string inspection (unreliable)
     * Query structure inspection (too complex)
   - Next steps:
     * Research SQLAlchemy test patterns for complex queries
     * Consider mock-alchemy library for better query mocking
     * Evaluate test structure reorganization
     * Document query patterns and expected returns
     * Consider moving complex query tests to integration tests

2. Model Access Pattern (Resolved)
   - test_health_check and test_cors_middleware: PASSING
   - Solution implemented:
     * Session-scoped event loop and engine fixtures
     * Function-scoped database session with proper transaction management
     * Improved cleanup between tests

2. Response Validation (Future Tasks)
   - test_concurrent_version_creation
   - test_version_creation_constraints
   - test_file_operation_constraints
   - test_partial_version_creation_rollback
   - test_concurrent_connection_pool_exhaustion
   - test_concurrent_version_state_race
   - test_idempotent_version_creation
   - test_file_operation_compensation
   - test_inactive_project_operations
   - test_inactive_project_version_operations
   Issue: Missing required fields (id, active, created_at, updated_at)

3. Implementation Error
   - test_create_version_with_changes
   - Issue: NameError (test_db not defined)

## Active Decisions

### Project State Management
1. Active State:
   - Projects are active by default
   - Soft deletion deactivates projects
   - Reactivation through update endpoint
   - Write operations blocked when inactive

2. Version Behavior:
   - Versions inherit project state
   - Empty list returned for inactive projects
   - No independent version activation
   - Read operations remain available

3. Operation Restrictions:
   - Write operations blocked on inactive projects
   - Read operations show inactive state
   - Reactivation allowed through PUT endpoint
   - PATCH operations not supported

## Current Focus
- Fixing SQLAlchemy mock response types in edge case tests
- Implementing query-based mock returns
- Ensuring correct model types in test responses
- Documenting mocking patterns and best practices
- Resolving remaining edge case test failures

## Test Organization
1. Directory Structure:
   ```
   api/tests/
   ├── unit_tests/          # Mock-dependent tests
   │   ├── conftest.py      # Unit test fixtures
   │   ├── test_edge_cases.py  # Currently failing
   │   ├── test_concurrent_operations.py
   │   └── test_inactive_project.py
   └── integration_tests/   # Real dependency tests
       ├── conftest.py      # Integration test fixtures
       ├── test_concurrent.py
       └── test_integration.py
   ```

2. Mock Implementation:
   ```python
   # Current Issue (Bad Pattern):
   @pytest.fixture(params=["project", "version"])
   def mock_db(request):
       result = MagicMock()
       if request.param == "project":
           result.scalar_one_or_none = lambda: mock_project
       else:
           result.scalar_one_or_none = lambda: mock_version
       return result

   # Needed Pattern:
   async def mock_execute(query):
       if "Project.active" in str(query):
           return MagicMock(scalar_one=lambda: True)
       if "ProjectVersion" in str(query):
           return MagicMock(
               unique=lambda: self,
               scalar_one_or_none=lambda: mock_version
           )
       return MagicMock(
           scalar_one_or_none=lambda: mock_project
       )
   ```

2. Current Issues:
   - Mock returns wrong model types for queries
   - Query type detection needs improvement
   - Response validation errors in unit tests
   - Transaction state conflicts in concurrent tests

3. Next Actions:
   - Implement query-based mock returns
   - Add test coverage for mock behavior
   - Fix response validation by including all required fields
   - Add transaction completion checks

## Recent Changes
1. Error Handling:
   - Simplified error propagation
   - Standardized status code mapping:
     * ValueError -> 400 Bad Request
     * IntegrityError -> 409 Conflict
     * OperationalError -> 503 Service Unavailable
   - Improved transaction rollback
   - Enhanced error messages

2. Testing Improvements:
   - Added edge case test coverage
   - Implemented dependency injection patterns
   - Enhanced service mocking
   - Verified error propagation
   - Added transaction rollback tests

3. Service Integration:
   - Improved OpenRouter service mocking
   - Enhanced error validation
   - Added test fixtures
   - Documented mocking patterns

## Pending Decisions
1. Pydantic Validation:
   - Consider updating to v2 methods
   - Review deprecation warnings
   - Plan migration strategy

2. API Documentation:
   - Document state behavior
   - Clarify operation restrictions
   - Update response examples

## Current Workflows
1. Project Operations:
   ```
   GET /api/projects/ - List active projects
   POST /api/projects/ - Create project
   GET /api/projects/{id} - Get project
   PUT /api/projects/{id} - Update project
   DELETE /api/projects/{id} - Soft delete
   ```

2. Version Operations:
   ```
   GET /api/projects/{id}/versions - List versions (empty if project inactive)
   POST /api/projects/{id}/versions - Create version (403 if project inactive)
   GET /api/projects/{id}/versions/{number} - Get version (includes active state)
   ```
