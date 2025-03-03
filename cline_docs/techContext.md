# Technical Context

## Technologies
- **FastAPI:** Web framework for building the API
- **SQLAlchemy:** Database toolkit and ORM
- **PostgreSQL:** Relational database via Supabase
- **Pydantic:** Data validation and settings management
- **pytest:** Testing framework
- **OpenRouter:** AI service integration for code generation

## Development Setup
- Python 3.11+
- Virtual environment (venv)
- Dependencies managed via `requirements.txt`
- Database connection configured via environment variables
- Supabase for local PostgreSQL database

### Database Connection Configuration
- **Connection URL Format**: `postgresql+asyncpg://[user]:[password]@[host]:[port]/[database]`
- **Production Example**: `postgresql+asyncpg://postgres:postgres@127.0.0.1:54342/postgres`
- Use `127.0.0.1` instead of `localhost` for reliable connections

### Application Startup Sequence
1. Start Supabase: `supabase start`
2. Apply migrations: `supabase db reset`
3. Start FastAPI application:
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54342/postgres uvicorn api.app.main:app --reload
   ```
4. Access API at http://localhost:8000/api/
5. Access API testing endpoint at http://localhost:8000/api-tester

## API Documentation

### Base URL
```
http://127.0.0.1:8000
```

### Key Endpoints

#### Health Check
- `GET /health` - Check if API is running

#### Projects
- `GET /api/projects/` - List all projects
- `POST /api/projects/` - Create a new project
- `GET /api/projects/{project_id}` - Get a specific project
- `PUT /api/projects/{project_id}` - Update a project
- `DELETE /api/projects/{project_id}` - Soft delete a project

#### Versions
- `GET /api/projects/{project_id}/versions/` - List all versions of a project
- `GET /api/projects/{project_id}/versions/{version_number}` - Get a specific version
- `POST /api/projects/{project_id}/versions/` - Create a new version

### Version Creation Request Format
```json
{
  "name": "New Version",
  "parent_version_number": 0,
  "project_context": "This is a React project with a simple component structure.",
  "change_request": "Add a new button component with onClick functionality."
}
```

### Current Limitations
- Creating new versions requires the OpenRouter service
- OpenRouter service is currently returning a 503 Service Unavailable error
- All other API endpoints are working correctly

## OpenRouter Integration
- Uses google/gemini-2.0-flash-001 model
- Responses wrapped in `<noodle_response>` tags
- JSON structure for file changes
- Environment-based API key configuration

## Version 0 Template System
- Located at api/templates/version-0/
- Structured as a complete TypeScript React project
- Files read during project creation
- Maintains relative paths from template root
