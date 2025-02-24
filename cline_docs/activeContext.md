# Active Context

## Current State
Currently addressing test failures with a focus on transaction management issues in concurrent operations.

## Test Failures (In Priority Order)
1. Event Loop Management (Current Focus)
   - test_create_project_with_version_0[trio]: RuntimeError with event loop
   - Error: "Task got Future attached to a different loop"
   - Root cause: Event loop sharing between tests
   - Solution in progress: Proper event loop configuration and cleanup

2. Transaction Management
   - test_health_check and test_cors_middleware: InterfaceError with asyncpg
   - Error: "cannot perform operation: another operation is in progress"
   - Root cause: Concurrent operation conflicts
   - Solution: Need proper transaction isolation and connection state management

3. Model Access Pattern
   - Resolved: test_create_project_with_version_0[asyncio]
   - Solution implemented:
     * Removed duplicate relationship definition
     * Using selectin loading strategy
     * Converted hybrid_property to regular property
     * Calculating latest_version_number from loaded data

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
- Improving error handling patterns
- Enhancing test coverage for edge cases
- Implementing service mocking standards
- Maintaining transaction integrity
- Fixing test organization issues
- Resolving concurrent test failures

## Test Organization
1. Directory Structure:
   ```
   api/tests/
   ├── unit_tests/          # Mock-dependent tests
   │   ├── conftest.py      # Unit test fixtures
   │   ├── test_edge_cases.py
   │   ├── test_concurrent_operations.py
   │   └── test_inactive_project.py
   └── integration_tests/   # Real dependency tests
       ├── conftest.py      # Integration test fixtures
       ├── test_concurrent.py
       └── test_integration.py
   ```

2. Current Issues:
   - Response validation errors in unit tests
   - Transaction state conflicts in concurrent tests
   - JSON syntax errors in test data
   - Need to properly mock response data

3. Next Actions:
   - Fix response validation by including all required fields
   - Add transaction completion checks
   - Fix JSON syntax in test requests
   - Update mock_db fixture to handle validation

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
