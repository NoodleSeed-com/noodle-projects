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

Once the server is running, you can access:
- Interactive API documentation (Swagger UI) at http://localhost:8000/docs
- Alternative API documentation (ReDoc) at http://localhost:8000/redoc

## Core API Endpoints

### Projects

- `GET /api/v1/projects` - List all active projects
- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects/{project_id}` - Get a specific project
- `PUT /api/v1/projects/{project_id}` - Update a project
- `DELETE /api/v1/projects/{project_id}` - Soft delete a project

### Project Versions

- `GET /api/v1/projects/{project_id}/versions` - List all versions of a project
- `POST /api/v1/projects/{project_id}/versions` - Create a new version
- `GET /api/v1/projects/{project_id}/versions/{version_number}` - Get a specific version
- `GET /api/v1/projects/{project_id}/versions/{version_number}/files` - List all files in a version
- `GET /api/v1/projects/{project_id}/versions/{version_number}/files/{file_path}` - Get a specific file

### Version Creation

- `POST /api/v1/projects/{project_id}/versions/{version_number}/files` - Create or update a file
- `POST /api/v1/projects/{project_id}/versions` - Create a new version from a parent version

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