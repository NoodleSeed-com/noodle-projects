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
- Non-negative integers only (>= 0)
- Unique within each project
- Version 0 reserved for initial version
- Enforced by database constraints

## Resolved Issues

-   The project was initially set up with asynchronous SQLAlchemy (asyncpg) and FastAPI endpoints, which caused compatibility issues with the synchronous `TestClient` used in the tests.
-   Switching to a fully synchronous approach has resolved these issues.

## Potential Solutions (No Longer Needed)

-   ~~Fully Asynchronous Approach: Keep the application code asynchronous and modify the tests to use `pytest-asyncio` correctly, ensuring proper event loop management and using an async test client like `httpx.AsyncClient`. This might require more complex test setup.~~
