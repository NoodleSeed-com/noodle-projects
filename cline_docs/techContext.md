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

## Validation Constraints

### File Path Validation
1. Application Level:
   - Empty paths rejected in File model's __init__
   - Raises ValueError with message "File path cannot be empty"
   - Prevents invalid data from reaching database
   - Implemented in SQLAlchemy model for immediate validation

2. Database Level:
   - CHECK constraint: `length(path) > 0`
   - UNIQUE constraint on (project_version_id, path)
   - Enforces path uniqueness within versions
   - Allows same path across different versions
   - Implemented in both SQLAlchemy model and database schema

### Version Number Validation
1. Model Level:
   - Validation in ProjectVersion.__init__
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

## Resolved Issues

-   The project was initially set up with asynchronous SQLAlchemy (asyncpg) and FastAPI endpoints, which caused compatibility issues with the synchronous `TestClient` used in the tests.
-   Switching to a fully synchronous approach has resolved these issues.
-   Version number validation now happens at multiple layers for better error handling.
-   CORS testing updated to match FastAPI's actual behavior.

## Potential Solutions (No Longer Needed)

-   ~~Fully Asynchronous Approach: Keep the application code asynchronous and modify the tests to use `pytest-asyncio` correctly, ensuring proper event loop management and using an async test client like `httpx.AsyncClient`. This might require more complex test setup.~~

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
