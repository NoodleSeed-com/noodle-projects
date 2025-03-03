# NoodleSeed API

A FastAPI microservice for managing software projects, their versions, and associated files. This API enables creation and management of project templates with version control.

## Overview

This service provides a RESTful API for:
- Creating and managing software projects with complete version control
- File-level version management with parent-child relationships
- Template-based project initialization (React/TypeScript by default)
- Optional AI-assisted code modification using OpenRouter

## Features

- **Project Management**
  - Create, read, update, and delete projects
  - Project-level active state management
  - Soft deletion support
  - Latest version tracking

- **Version Control**
  - Automatic version 0 template initialization
  - Parent-child version relationships
  - Version-specific file management
  - Unique version numbers per project

- **File Management**
  - File content versioning
  - Path uniqueness validation
  - Bulk file operations
  - Template-based initialization

- **AI Integration** (Optional)
  - Code generation using OpenRouter API
  - Structured response format
  - Template-aware suggestions
  - Context-based code modifications

- **MCP Integration** (Model Context Protocol)
  - Direct AI assistant access to API functionality
  - Identical business logic between REST and MCP
  - Standardized tool descriptions and error handling
  - Local MCP server testing capabilities

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd noodle-projects
   ```

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r api/requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp api/.env.example api/.env
   # Edit .env with your database credentials and optional API keys
   ```

   The application requires these environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `OPENROUTER_API_KEY`: (Optional) For AI code generation features
   - `TEST_DATABASE_URL`: For test database connection

5. **Run the development server**:
   ```bash
   uvicorn api.app.main:app --reload
   ```

## API Documentation

### Base URL

```
http://127.0.0.1:8000
```

### Authentication

Currently, the API does not require authentication.

### API Endpoints

#### Health Check

**Endpoint:** `GET /health`

**Description:** Check if the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

#### Projects

##### List Projects

**Endpoint:** `GET /api/projects/`

**Description:** Get a list of all projects.

**Response:**
```json
[
  {
    "name": "Project Name",
    "description": "Project Description",
    "id": "uuid-string",
    "latest_version_number": 0,
    "active": true,
    "created_at": "2025-02-28T01:17:42.699132Z",
    "updated_at": "2025-02-28T01:17:42.699132Z"
  },
  ...
]
```

##### Create Project

**Endpoint:** `POST /api/projects/`

**Description:** Create a new project.

**Request Body:**
```json
{
  "name": "My Test Project",
  "description": "A project created for testing"
}
```

**Response:**
```json
{
  "name": "My Test Project",
  "description": "A project created for testing",
  "id": "uuid-string",
  "latest_version_number": 0,
  "active": true,
  "created_at": "2025-02-28T01:18:56.895531Z",
  "updated_at": "2025-02-28T01:18:56.895531Z"
}
```

**Notes:** 
- A version 0 is automatically created when a project is created.
- The `description` field is optional.

##### Get Project

**Endpoint:** `GET /api/projects/{project_id}`

**Description:** Get details of a specific project.

**Response:**
```json
{
  "name": "Project Name",
  "description": "Project Description",
  "id": "uuid-string",
  "latest_version_number": 0,
  "active": true,
  "created_at": "2025-02-28T01:17:42.699132Z",
  "updated_at": "2025-02-28T01:17:42.699132Z"
}
```

##### Update Project

**Endpoint:** `PUT /api/projects/{project_id}`

**Description:** Update a project's details.

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "This project has been updated"
}
```

**Response:** Updated project object.

##### Delete Project

**Endpoint:** `DELETE /api/projects/{project_id}`

**Description:** Soft delete a project by setting active=false.

**Response:** The deactivated project object.

#### Versions

##### List Versions

**Endpoint:** `GET /api/projects/{project_id}/versions/`

**Description:** Get a list of all versions for a project.

**Response:**
```json
[
  {
    "id": "uuid-string",
    "version_number": 0,
    "name": "Initial Version"
  },
  ...
]
```

##### Get Version

**Endpoint:** `GET /api/projects/{project_id}/versions/{version_number}`

**Description:** Get details of a specific version.

**Response:**
```json
{
  "id": "uuid-string",
  "project_id": "project-uuid-string",
  "version_number": 0,
  "name": "Initial Version",
  "parent_id": null,
  "parent_version": null,
  "created_at": "2025-02-28T01:17:42.699132Z",
  "updated_at": "2025-02-28T01:17:42.699132Z",
  "active": true,
  "files": [
    {
      "id": "file-uuid-string",
      "version_id": "version-uuid-string",
      "path": "src/App.tsx",
      "content": "// File content here",
      "created_at": "2025-02-28T01:17:42.699132Z",
      "updated_at": "2025-02-28T01:17:42.699132Z"
    },
    ...
  ]
}
```

##### Create Version

**Endpoint:** `POST /api/projects/{project_id}/versions/`

**Description:** Create a new version based on an existing version.

**Request Body:**
```json
{
  "name": "New Version",
  "parent_version_number": 0,
  "project_context": "This is a React project with a simple component structure.",
  "change_request": "Add a new button component with onClick functionality."
}
```

**Response:** The newly created version object with files.

**Notes:**
- This endpoint requires the OpenRouter service to generate file changes.
- Currently, this endpoint returns a 503 Service Unavailable error due to issues with the OpenRouter service.
- All fields in the request body are required.
- `parent_version_number` specifies which version to base the new version on.
- `project_context` provides context about the project for the AI.
- `change_request` specifies what changes to make in the new version.

### Error Handling

The API uses standard HTTP status codes:

- 200: Success
- 400: Bad Request (validation errors)
- 403: Forbidden (e.g., trying to modify an inactive project)
- 404: Not Found (resource doesn't exist)
- 422: Unprocessable Entity (request validation errors)
- 503: Service Unavailable (e.g., OpenRouter service unavailable)

Error responses have the following format:

```json
{
  "detail": "Error message"
}
```

### Current Limitations

- Creating new versions through the API requires the OpenRouter service
- OpenRouter service is currently returning a 503 Service Unavailable error
- All other API endpoints are working correctly

### Example Usage (Python)

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Create a new project
project_data = {
    "name": "My Test Project",
    "description": "A project created for testing"
}
response = requests.post(f"{BASE_URL}/api/projects/", json=project_data)
project = response.json()
project_id = project["id"]

# List versions of the project
response = requests.get(f"{BASE_URL}/api/projects/{project_id}/versions/")
versions = response.json()
version_number = versions[0]["version_number"]  # Usually 0 for a new project

# Get details of a specific version
response = requests.get(f"{BASE_URL}/api/projects/{project_id}/versions/{version_number}")
version_details = response.json()

# Try to create a new version (will fail with 503 until OpenRouter service is fixed)
new_version_data = {
    "name": "New Version",
    "parent_version_number": version_number,
    "project_context": "This is a React project with a simple component structure.",
    "change_request": "Add a new button component with onClick functionality."
}
try:
    response = requests.post(
        f"{BASE_URL}/api/projects/{project_id}/versions/",
        json=new_version_data
    )
    if response.status_code == 503:
        print("OpenRouter service unavailable")
    else:
        new_version = response.json()
except Exception as e:
    print(f"Error creating version: {e}")
```

You can also access:
- Interactive API documentation (Swagger UI) at http://localhost:8000/docs
- Alternative API documentation (ReDoc) at http://localhost:8000/redoc

## Database Schema

The service uses three main tables:

1. `projects` - Stores project metadata
   - `id`: UUID (Primary Key)
   - `name`: Text (Required)
   - `description`: Text (Required, defaults to empty string)
   - `latest_version_number`: Integer (Computed, returns highest version number)
   - `active`: Boolean (Required, defaults to true)
   - `created_at`: Timestamp with timezone
   - `updated_at`: Timestamp with timezone

2. `versions` - Stores project versions
   - `id`: UUID (Primary Key)
   - `project_id`: UUID (Foreign Key to projects, CASCADE on delete)
   - `version_number`: Integer (Required, defaults to 0, unique per project)
   - `parent_id`: UUID (Optional, Foreign Key to versions)
   - `name`: Text (Required, defaults to empty string)
   - `created_at`: Timestamp with timezone
   - `updated_at`: Timestamp with timezone
   - Constraints:
     * UNIQUE(project_id, version_number)
     * Index on (project_id, version_number) for faster lookups

3. `files` - Stores files associated with project versions
   - `id`: UUID (Primary Key)
   - `version_id`: UUID (Foreign Key to versions)
   - `path`: Text (Required)
   - `content`: Text (Required)
   - `created_at`: Timestamp with timezone
   - `updated_at`: Timestamp with timezone

## Project Structure

```
api/
├── app/
│   ├── config.py            # Application configuration
│   ├── crud/               # Database operations
│   │   ├── file.py         # File CRUD operations
│   │   ├── project.py      # Project CRUD operations
│   │   └── version/        # Version-related operations
│   │       ├── crud.py     # Version CRUD
│   │       ├── file_operations.py  # File manipulation
│   │       └── template.py # Template handling
│   ├── main.py             # Application entry point
│   ├── models/             # SQLAlchemy models
│   │   ├── base.py         # Base model class
│   │   ├── file.py         # File model
│   │   ├── project.py      # Project model
│   │   └── version.py      # Version model
│   ├── routes/             # API endpoints
│   │   ├── projects.py     # Project routes
│   │   └── versions.py     # Version routes
│   ├── schemas/            # Pydantic schemas
│   │   ├── base.py         # Base schema class
│   │   ├── common.py       # Shared schemas
│   │   ├── file.py         # File schemas
│   │   ├── project.py      # Project schemas
│   │   └── version.py      # Version schemas
│   └── services/           # External services
│       └── openrouter.py   # OpenRouter AI integration
├── templates/              # Project templates
│   └── version-0/          # Default template (React/TypeScript)
└── tests/                  # Test suite
    ├── integration_tests/  # Integration tests
    └── unit_tests/         # Unit tests
```

## Integration with Other Services

Other microservices can integrate with the NoodleSeed API in the following ways:

### HTTP Client Integration

Python services can use libraries like `httpx` or `requests` to interact with the API:

```python
import httpx

class NoodleSeedClient:
    def __init__(self, base_url="http://localhost:8000/api/v1", api_key=None):
        self.base_url = base_url
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            
    async def get_projects(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
            
    async def create_project(self, name, description=""):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/projects",
                headers=self.headers,
                json={"name": name, "description": description}
            )
            response.raise_for_status()
            return response.json()
            
    async def get_version_files(self, project_id, version_number):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/versions/{version_number}/files",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
```

### FastAPI Service Integration

Services built with FastAPI can include the NoodleSeed API as a dependency:

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import httpx
from typing import List

app = FastAPI()

class NoodleSeedService:
    def __init__(self):
        self.base_url = "http://noodleseed-api:8000/api/v1"  # Docker service name
        
    async def get_project(self, project_id: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/projects/{project_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Project not found")
                raise HTTPException(status_code=500, detail="Error connecting to NoodleSeed API")

def get_noodleseed_service():
    return NoodleSeedService()

@app.get("/templates/{project_id}")
async def get_template(
    project_id: str,
    noodleseed: NoodleSeedService = Depends(get_noodleseed_service)
):
    project = await noodleseed.get_project(project_id)
    return {"template_info": project}
```

### Event-Driven Integration

For asynchronous integration, services can use events with a message broker:

```python
import asyncio
import json
from fastapi import FastAPI, BackgroundTasks
import httpx
from redis import Redis

app = FastAPI()
redis = Redis(host="redis", port=6379)

async def process_project_update(project_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://noodleseed-api:8000/api/v1/projects/{project_id}")
        if response.status_code == 200:
            project_data = response.json()
            # Process project data
            redis.publish("project_updates", json.dumps({
                "project_id": project_id,
                "name": project_data["name"],
                "latest_version": project_data["latest_version_number"]
            }))

@app.post("/notify/project_update/{project_id}")
async def notify_project_update(project_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_project_update, project_id)
    return {"status": "Update notification received"}
```

### Container-Based Deployment

For containerized environments, use Docker Compose for communication:

```yaml
# docker-compose.yml
version: '3'
services:
  noodleseed-api:
    image: noodleseed-api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/noodleseed
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - db
      
  your-service:
    build: .
    environment:
      - NOODLESEED_API_URL=http://noodleseed-api:8000/api/v1
    depends_on:
      - noodleseed-api
      
  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=noodleseed
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
pytest api/tests/path/to/test_file.py -v

# Run specific test function
pytest api/tests/path/to/test_file.py::test_function_name -v
```

### Using MCP (Model Context Protocol)

```bash
# Install MCP dependencies
pip install -r api/requirements.txt

# Test MCP server locally
PYTHONPATH=. python api/test_mcp_local.py

# Run MCP server in development mode
PYTHONPATH=. mcp dev api/app/mcp_server.py

# Use with Claude Desktop
# Configure Claude Desktop to use the MCP server:
# 1. Locate the Claude Desktop config file:
#    - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
#    - Windows: %APPDATA%\Claude\claude_desktop_config.json
# 2. Add your MCP server to the configuration following the example in mcp_capability.md
```

### Code Style Guidelines

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

## Contributing

1. Ensure all tests pass before submitting changes
2. Follow coding style guidelines in the codebase
3. Add tests for new features to maintain coverage
4. Update documentation when making significant changes

## License

[Specify license information]
