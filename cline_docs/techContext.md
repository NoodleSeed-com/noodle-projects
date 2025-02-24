# Technical Context

## Technologies

-   **FastAPI:** Web framework for building the API.
-   **SQLAlchemy:** Database toolkit and ORM.
-   **PostgreSQL:** Relational database.
-   **Pydantic:** Data validation and settings management.
-   **pytest:** Testing framework.
-   **httpx:** HTTP client (used by FastAPI's TestClient).
-   **psycopg2-binary:** `psycopg2-binary` (for synchronous operations)
-   **dotenv:** For loading environment variables.
-   **OpenRouter:** AI service integration for code generation.

## Development Setup

-   Python 3.11+
-   Virtual environment (venv)
-   Dependencies managed via `requirements.txt`
-   Database connection configured via environment variables (`DATABASE_URL`, etc.)
-   Test environment variables in `api/tests/test.env`

## Technical Decisions

-   The project has been switched to a fully synchronous approach for both the application and the tests.
-   This simplifies the test setup and avoids compatibility issues between synchronous tests and asynchronous database operations.
-   Multi-layer validation strategy for robust data integrity.
-   CORS configuration optimized for development flexibility.

## Dependencies

-   **FastAPI:** `fastapi`
-   **SQLAlchemy:** `sqlalchemy`
-   **psycopg2-binary:** `psycopg2-binary` (for synchronous operations)
-   **Pydantic:** `pydantic`
-   **pytest:** `pytest`
-   **httpx:** `httpx`
-   **python-dotenv:** `python-dotenv`
-   **openrouter-py:** OpenRouter API client

## Validation Constraints

### File Path Validation
1. Application Level:
   - Empty paths rejected in File model's __init__
   - Raises ValueError with message "File path cannot be empty"
   - Prevents invalid data from reaching database
   - Implemented in SQLAlchemy model for immediate validation

2. Database Level:
   - CHECK constraint: `length(path) > 0`
   - UNIQUE constraint on (version_id, path)
   - Enforces path uniqueness within versions
   - Allows same path across different versions
   - Implemented in both SQLAlchemy model and database schema

### Version Number Validation
1. Model Level:
   - Validation in Version.__init__
   - Raises IntegrityError for negative numbers
   - Early validation before database operations
   - Clear error messages for debugging

2. Database Level:
   - CHECK constraint: `version_number >= 0`
   - UNIQUE constraint on (project_id, version_number)
   - Version 0 reserved for initial version
   - Enforced by database schema

3. API Level:
   - Path parameter validation in FastAPI routes
   - Automatic validation of version number format
   - Returns 422 for invalid version numbers
   - Consistent error handling across endpoints

## CORS Configuration

### Development Settings
- BACKEND_CORS_ORIGINS = ["*"] for development flexibility
- Configured in Settings class using Pydantic

### FastAPI CORSMiddleware Behavior
- When allow_origins=["*"], origin is reflected back
- Response includes actual requesting origin in access-control-allow-origin
- Example: Request from "http://localhost" gets "http://localhost" in response
- Maintains security while allowing development access

### Testing Considerations
- CORS tests must account for origin reflection
- Test both preflight (OPTIONS) and actual requests
- Verify correct headers in responses
- Check allowed methods and headers

## OpenRouter Integration

### Service Configuration
- Uses google/gemini-2.0-flash-001 model
- Environment-based API key configuration
- Response validation with Pydantic models
- Proper error handling and logging

### Response Format
- Responses wrapped in `<noodle_response>` tags
- JSON structure for file changes:
  ```json
  {
    "changes": [{
      "operation": "create|update|delete",
      "path": "relative/file/path",
      "content": "string"
    }]
  }
  ```
- File paths relative to project root
- Content properly escaped in JSON

### Service Pattern
- Dependency injection for service access
- Centralized service configuration
- Test mode support
- Comprehensive error handling

### Testing Strategy
- Mock service in test environment
- Override dependencies in tests
- Verify service calls with flexible assertions
- Clear mock overrides after tests

## Version 0 Template System

### Implementation Details
1. Template Location:
   - Located at api/templates/version-0/
   - Structured as a complete TypeScript React project
   - Files are read during project creation

2. File Loading:
   ```python
   template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'version-0')
   for root, _, files in os.walk(template_dir):
       for file in files:
           file_path = os.path.join(root, file)
           relative_path = os.path.relpath(file_path, template_dir)
           with open(file_path, 'r') as f:
               content = f.read()
           db_file = File(
               version_id=version.id,
               path=relative_path,
               content=content
           )
   ```

3. Path Handling:
   - Uses os.path for cross-platform compatibility
   - Maintains relative paths from template root
   - Preserves directory structure in database

4. Testing:
   - Comprehensive test suite in test_versions.py
   - Verifies file structure matches template
   - Validates file contents are copied correctly
   - Tests run in CI/CD pipeline

### Technical Considerations
1. File System:
   - Template files read synchronously
   - UTF-8 encoding assumed for all files
   - Directory structure preserved in database

2. Database Impact:
   - Files created in single transaction
   - Bulk insert for better performance
   - Maintains referential integrity

3. Error Handling:
   - File read errors caught and logged
   - Transaction rollback on failure
   - Clear error messages for debugging

## Test Coverage

### Current Coverage (97%)
- app/__init__.py: 100%
- app/config.py: 100%
- app/crud.py: 98%
- app/main.py: 100%
- app/models/base.py: 100%
- app/models/project.py: 98%
- app/projects.py: 91%

### Coverage Strategy
- Maintain minimum 80% overall coverage
- Critical paths require 100% coverage
- Models require 100% coverage
- Edge cases and error conditions must be tested
- Regular coverage monitoring in CI/CD

### Critical Path Testing
The most critical integration test verifies the core project creation flow:
```python
# In test_main.py
def test_create_project_with_version_0(client):
    """Core integration test that verifies project creation flow."""
    # Tests complete flow from project creation to version retrieval
    # Ensures version 0 template system works correctly
    # Verifies API endpoints, database operations, and file handling
```

This test is essential because:
- Tests the foundational project creation operation
- Verifies automatic version 0 creation
- Validates template file system
- Ensures API endpoints work correctly
- Confirms database integration
- Represents the most common user flow
