# Active Context

## Current State
The project is in a stable state with all tests passing. Recent changes have focused on improving the handling of inactive projects and their versions.

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
