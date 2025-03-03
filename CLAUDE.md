# Claude Assistant Guide for Noodle Projects

## Build & Test Commands
- Install: `pip install -r api/requirements.txt`
- Run server: `uvicorn app.main:app --reload`
- Test all: `pytest`
- Test with coverage: `pytest --cov=app --cov-report=term-missing --cov-report=html`
- Test specific file: `pytest api/tests/path/to/test_file.py -v`
- Test specific function: `pytest api/tests/path/to/test_file.py::test_function_name -v`

## MCP Commands
- Test MCP server: `PYTHONPATH=. python api/test_mcp_local.py`
- Test MCP with Supabase (REST API): `PYTHONPATH=. python api/test_mcp_rest.py`
- Test MCP with direct Supabase connection: `PYTHONPATH=. python api/check_supabase_conn.py`
- Run MCP server with REST API: `PYTHONPATH=. mcp dev api/app/mcp_server_rest.py`
- Run MCP server with direct connection: `PYTHONPATH=. mcp dev api/app/mcp_server.py`
- Inspect MCP server: `mcp inspect http://localhost:8555`

## Supabase Connection
- Preferred method: Use Supabase REST API (`python api/test_mcp_with_supabase_rest.py`)
- Alternative: Transaction mode for serverless/testing: `postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?ssl=true&prepared_statement_cache_size=0`
- Test all connection methods: `python api/check_supabase_conn.py`
- Documentation: See `api/docs/supabase_connection.md` for details

## Claude Desktop MCP Integration

### Configure Claude Desktop
Add Noodle Projects to your Claude Desktop configuration:

1. Find your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add to the `mcpServers` section:
```json
"noodle-projects": {
  "command": "mcp",
  "args": ["run", "/path/to/noodle-projects/api/app/mcp_server_rest.py"],
  "env": {
    "PYTHONPATH": "/path/to/noodle-projects",
    "SUPABASE_URL": "https://jsanjojgtyyfpnfqwhgx.supabase.co",
    "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM"
  }
}
```

3. Start Claude Desktop and use: `/mcp noodle-projects`

See `api/docs/claude_desktop_setup.md` for detailed setup instructions.

### Available MCP Functions
- `check_health` - Check server health
- `list_projects` - List all projects
- `get_project` - Get project details by ID 
- `create_project` - Create a new project
- `update_project` - Update project details
- `delete_project` - Delete a project (soft delete)
- `list_versions` - List versions for a project
- `get_version` - Get version details
- `create_version` - Create a new version
- `get_file` - Get file contents
- `create_or_update_file` - Create or update a file

See `api/docs/claude_desktop_usage.md` for detailed usage instructions.

## Research Guidelines
- Use Perplexity proactively for:
  - Troubleshooting known issues and workarounds
  - Finding latest library/framework documentation
  - Accessing information updated since knowledge cutoff
  - Discovering technical solutions shared by the community

## Code Style Guidelines
- Follow PEP 8 guidelines with consistent indentation (4 spaces)
- Import order: stdlib → third-party → relative (alphabetical within groups)
- Type hints required for all functions/methods and return values
- Use snake_case for variables/functions, CamelCase for classes
- Async/await patterns throughout codebase
- Custom error handling with NoodleError exception class and ErrorType enum
- Comprehensive docstrings for all functions and classes
- SQL queries using SQLAlchemy ORM (not raw SQL)
- Tests required for all new features (minimum 80% coverage)
- API schemas defined with Pydantic v2
- Clear separation between models, schemas, and route handlers