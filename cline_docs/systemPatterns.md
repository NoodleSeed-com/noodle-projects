# System Patterns

## Microservice Best Practices

### Project Structure and Organization ✅
- Clear separation of concerns with distinct modules
- Co-located tests with source code
- Modular design with focused components

### API Design and Implementation ✅
- RESTful endpoint design with clear resource hierarchy
- Consistent response models with Pydantic
- Proper status code usage

### Database Design and ORM Usage ✅
- Proper use of SQLAlchemy ORM with async support
- Well-designed models with appropriate relationships
- Soft deletion through active flag

### Error Handling ✅
- Custom NoodleError class with error types
- Consistent error response format
- Proper mapping of error types to HTTP status codes

### Testing Approach ✅
- Comprehensive test coverage (97%)
- Clear test organization with co-located tests
- Transaction isolation for test independence

### Async Implementation ⚠️
- SQLAlchemy event listener issue with async functions
- Needs pattern for handling async functions in event listeners

### Recommendations
1. Fix SQLAlchemy event listener issue using synchronous listener with asyncio.create_task()
2. Add API versioning for future compatibility
3. Enhance error types for better client feedback
4. Add rate limiting for API endpoints
5. Improve authentication mechanisms

## Test Organization Patterns

### Co-located Tests Pattern
```
api/app/
├── models/
│   ├── model.py
│   └── tests/              # Model tests
├── routes/
│   ├── route.py
│   └── tests/              # Route tests
└── services/
    ├── service.py
    └── tests/              # Service tests
```

### Test Database Setup Patterns
- Module-level database with proper cleanup
- Test-level transactions with savepoints
- Proper transaction isolation

### FastAPI Testing Best Practices
- Use separate test database (in-memory SQLite)
- Override dependencies for testing
- Use pytest-asyncio for async tests
- Implement transaction isolation

## SQLAlchemy Patterns

### Session Management
- Commit to trigger events, refresh to load relationships
- Handle unique constraints explicitly
- Use proper transaction boundaries
- Implement error handling with rollbacks

### Version Management Patterns
- Version 0 reserved for initial version
- Auto-create initial version on project creation
- Prefer soft delete for history preservation
- Test both Python and database-level validations

### SQLAlchemy Event Listeners with Async Functions
```python
# Separate the async implementation
async def async_create_initial_version(project_id, session):
    """Async implementation of initial version creation."""
    pass

# Create a synchronous event listener
def create_initial_version_listener(mapper, connection, target):
    """Synchronous event listener that schedules the async function."""
    asyncio.create_task(
        async_create_initial_version(
            target.id, 
            AsyncSession(bind=connection)
        )
    )

# Register the synchronous event listener
event.listen(Project, 'after_insert', create_initial_version_listener)
```
