# Claude Assistant Guide for Noodle Projects

## Build & Test Commands
- Install with UV: `uv pip install -r requirements.lock`
- Install with pip (legacy): `pip install -r api/requirements.txt`
- Run server: `uvicorn app.main:app --reload`
- Run all tests: `pytest`
- Run with coverage: `pytest --cov=app --cov-report=term-missing --cov-report=html`
- Run specific test: `pytest api/tests/path/to/test_file.py::test_function_name -v`
- Run tests by marker: `pytest -m unit` or `pytest -m integration`
- Debug mode: Add `-xvs` flag to see detailed output in real-time

## Test Environment Setup
- Tests use PostgreSQL with transaction isolation
- Unit tests (`-m unit`) use mock DB sessions
- Integration tests (`-m integration`) use real DB with transaction rollback
- External tests (`-m external`) call external APIs
- Required env vars in `.env` or `tests/.env`:
  - DATABASE_URL: PostgreSQL connection string
  - TEST_DATABASE_URL: Same as DATABASE_URL
  - TEST_MODE: Set to "true" for test environment

## Dependency Management
- Update lockfile: `uv pip compile api/requirements.txt -o requirements.lock`
- Install from lockfile: `uv pip install -r requirements.lock`
- Run tools without installing: `uvx [tool]` (e.g., `uvx black .`)

## MCP Commands
- Test Supabase client: `PYTHONPATH=. python api/test_supabase_official.py`
- Run MCP server: `PYTHONPATH=. mcp dev api/app/mcp_server_supabase.py`
- Inspect MCP server: `mcp inspect http://localhost:8555`

## Supabase Connection
- Uses official supabase-py client to interact with Supabase
- Configuration via environment variables:
  - `SUPABASE_URL`: Your Supabase project URL (required)
  - `SUPABASE_KEY`: Your Supabase API key (required)
- Both variables MUST be set before running any Supabase operations
- Test connection: `PYTHONPATH=. python api/test_supabase_official.py`

## Available MCP Functions
- `check_health` - Check server health
- `list_projects` - List all projects
- `get_project` - Get project details by ID 
- `create_project` - Create a new project
- `update_project` - Update project details
- `delete_project` - Delete a project (soft delete)
- `list_versions` - List versions for a project
- `get_version` - Get version details (includes files)
- `create_version` - Create a new version

Note: File operations are handled internally as part of version management.

## Code Style Guidelines
- PEP 8 compliant: 4-space indentation, 88-character line limit
- Import order: stdlib → third-party → relative (alphabetical)
- Type hints required for all functions and return values
- Naming: snake_case for variables/functions, CamelCase for classes
- Async/await patterns throughout codebase
- Error handling: Use NoodleError with appropriate ErrorType enum
- Docstrings: Required for all functions, classes, and modules
- Database: Use supabase-py client for all database operations
- Tests: Required for all features (80% coverage minimum)
- API schemas: Use Pydantic v2 models
- Clear separation between models, schemas, and route handlers