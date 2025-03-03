# Noodle Projects API

This is the backend API for the Noodle Projects application. It provides a REST API and an MCP server for managing projects, versions, and files.

## Setup for Local Development

### Prerequisites
- Python 3.11+
- Supabase account and project

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the `api` directory with the following variables:
```
# Database configuration - Choose one of these approaches:
# 1. Local PostgreSQL instance 
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres

# 2. Supabase REST API (preferred for most development)
SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_SERVICE_ROLE_KEY]

# OpenRouter API (optional)
OPENROUTER_API_KEY=your_openrouter_key
```

## Running the API Server

### FastAPI Server
```bash
cd api
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.
- API docs: http://localhost:8000/docs
- API tester: http://localhost:8000/static/api-tester.html

### MCP Server

#### Option 1: MCP with Supabase REST API (Recommended)
```bash
cd api
PYTHONPATH=. mcp dev app/mcp_server_rest.py
```

#### Option 2: MCP with direct database connection
```bash
cd api
PYTHONPATH=. mcp dev app/mcp_server.py
```

The MCP Inspector will be available at http://localhost:5173.

## Testing

### Run all tests
```bash
cd api
pytest
```

### Run integration tests
```bash
cd api
pytest tests/integration_tests/
```

### Run specific test file
```bash
cd api
pytest tests/integration_tests/test_main.py -v
```

### Test MCP with Supabase
```bash
cd api
# Test REST API implementation (recommended)
PYTHONPATH=. python test_mcp_rest.py

# Test direct connection
PYTHONPATH=. python check_supabase_conn.py
```

## Using with Claude Desktop

To use this API with Claude Desktop:

1. Ensure the MCP server is running:
```bash
cd api
PYTHONPATH=. mcp dev app/mcp_server_rest.py
```

2. In Claude Desktop, use the following command to connect:
```
/mcp http://localhost:5173
```

3. After connecting, you can use the MCP functions in your conversations with Claude:
```
/mcp list_projects
```

4. Available MCP functions:
- `list_projects`
- `get_project`
- `create_project`
- `update_project`
- `delete_project`
- `list_versions`
- `get_version`
- `create_version`
- `get_file`
- `create_or_update_file`
- `check_health`

## Documentation

- API docs: Available at http://localhost:8000/docs when the FastAPI server is running
- Supabase connection guide: `api/docs/supabase_connection.md`
- Claude Guide: See `CLAUDE.md` for common commands and development patterns