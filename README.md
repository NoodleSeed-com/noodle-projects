# Noodle Projects

A platform for managing coding projects with AI-powered version generation.

## Overview

This service provides a RESTful API for:
- Creating and managing software projects with complete version control
- File-level version management with parent-child relationships
- Template-based project initialization (React/TypeScript by default)
- Optional AI-assisted code modification using OpenRouter
- Claude Desktop integration via MCP (Model Context Protocol)

## API Structure

The API is organized as follows:

- `/api/app`: Main application code
  - `/crud`: CRUD operations for database entities
  - `/models`: SQLAlchemy ORM models
  - `/schemas`: Pydantic schemas for API
  - `/routes`: FastAPI route handlers
  - `/services`: External services integration
  - `/mcp`: MCP server implementations (unified)

## Running the API

1. Install dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```

2. Run the API server:
   ```bash
   cd api
   uvicorn app.main:app --reload
   ```

3. Run the MCP server:
   ```bash
   # For direct database access:
   PYTHONPATH=. mcp dev app/mcp/server.py

   # For Supabase REST API:
   NOODLE_DB_CONNECTION_TYPE=supabase_rest PYTHONPATH=. mcp dev app/mcp/server.py
   ```

## Testing

Run tests with:

```bash
pytest
```

For specific test modules:

```bash
pytest api/tests/path/to/test_file.py
```

## MCP Integration

Noodle Projects provides an MCP server that can be used with Claude Desktop:

1. Run the MCP server
2. Configure Claude Desktop to use the server
3. Use `/mcp noodle-projects` in Claude Desktop

See `CLAUDE.md` for detailed setup instructions.

## Database Options

Noodle Projects supports two database connection methods:

1. **Direct SQLAlchemy Connection**: For local development and testing
2. **Supabase REST API**: For serverless environments

Set the `NOODLE_DB_CONNECTION_TYPE` environment variable to `sqlalchemy` or `supabase_rest` to choose the connection method.

## Development

See `CLAUDE.md` for development guidelines and commands.