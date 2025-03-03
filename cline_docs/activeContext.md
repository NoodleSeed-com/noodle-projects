# Active Context

## Current State (Updated 2025-02-27)

### API Edge Cases and Testing
- **OpenRouter Authentication Issues**: 401 errors due to invalid/expired API key
- **Transaction Management Issues**: "A transaction is already begun on this Session" errors
- **Inactive Project Operations**: Cannot modify inactive projects without reactivation
- **Version Creation Requirements**: All fields required, parent version must exist
- **OpenRouter Service Testing**: Requires proper async handling and environment setup

### API Testing Methods
- API tester interface at http://localhost:8000/api-tester
- Comprehensive CLI testing examples with curl
- Documented reactivation process for inactive projects

### Environment Configuration
- Database URL: `postgresql+asyncpg://postgres:postgres@127.0.0.1:54342/postgres`
- Use `127.0.0.1` instead of `localhost` for reliable connections
- OpenRouter service currently returning 503 Service Unavailable error

### Application Status
- Successfully started and reset Supabase
- Started FastAPI service with correct database connection
- All API endpoints working except version creation (OpenRouter issue)
- Created several projects through the API
- Each project automatically initialized with version 0 containing template files

### Known Issues
- Creating new versions requires OpenRouter service (currently unavailable)
- SQLAlchemy event listener issue with async functions
- Coroutine 'create_initial_version' was never awaited warning

### Recent Improvements
- Fixed database connection configuration
- Improved file organization
- Enhanced API documentation
- Fixed API tester version creation sample
