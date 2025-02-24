# Progress Report

## Test Status

### Passing Tests
- test_create_project_with_version_0[asyncio]: Successfully fixed by:
  - Removing duplicate relationship definition in Project model
  - Using selectin loading strategy for versions relationship
  - Converting hybrid_property to regular property for latest_version_number

### Remaining Test Failures
1. test_create_project_with_version_0[trio]
   - Issue: RuntimeError with event loop and task management
   - Error: "Task got Future attached to a different loop"

2. test_health_check[asyncio/trio]
   - Issue: InterfaceError with asyncpg
   - Error: "cannot perform operation: another operation is in progress"

3. test_cors_middleware[asyncio/trio]
   - Issue: Same InterfaceError as health_check tests
   - Error: "cannot perform operation: another operation is in progress"

## Recent Changes

1. Project Model Improvements:
   - Removed duplicate versions relationship
   - Implemented eager loading with selectin strategy
   - Simplified latest_version_number calculation

2. Database Access Pattern:
   - Changed from hybrid_property to regular property
   - Ensures versions are pre-loaded via selectin strategy
   - Avoids async operation in property getter

## Next Steps

1. Event Loop Management:
   - Need to investigate event loop configuration in pytest-asyncio
   - Consider session vs function scope for event loop fixture
   - Address loop sharing between asyncio and trio tests

2. Transaction Management:
   - Review transaction isolation in test database setup
   - Consider AUTOCOMMIT mode for test engine
   - Implement proper cleanup between tests

3. Connection Handling:
   - Address concurrent operation issues with asyncpg
   - Review connection pooling configuration
   - Implement proper connection cleanup

## Test Infrastructure TODOs

1. Event Loop Configuration:
   - [ ] Configure proper event loop scope
   - [ ] Handle loop cleanup between tests
   - [ ] Address asyncio/trio compatibility

2. Database Setup:
   - [ ] Review transaction isolation levels
   - [ ] Implement proper connection pooling
   - [ ] Add connection cleanup handlers

3. Test Fixtures:
   - [ ] Refactor test_db fixture for better isolation
   - [ ] Add error handling in fixtures
   - [ ] Improve cleanup procedures
