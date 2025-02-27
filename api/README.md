# NoodleSeed API

A FastAPI microservice for managing software projects, their versions, and associated files. This API enables creation and management of project templates with version control.

## Features

- Project creation and management
- Version control with parent-child relationships
- File storage and retrieval
- Template-based project generation
- AI-assisted code modification

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd api
   ```

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and optional API keys
   ```

5. **Run the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Configuration

The application requires these environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENROUTER_API_KEY`: (Optional) For AI code generation features
- `TEST_DATABASE_URL`: For test database connection

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI) at http://localhost:8000/docs
- Alternative API documentation (ReDoc) at http://localhost:8000/redoc

## Core API Endpoints

### Projects

- `GET /projects` - List all active projects
- `POST /projects` - Create a new project
- `GET /projects/{project_id}` - Get a specific project
- `PUT /projects/{project_id}` - Update a project
- `DELETE /projects/{project_id}` - Soft delete a project

### Project Versions

- `GET /projects/{project_id}/versions` - List all versions of a project
- `POST /projects/{project_id}/versions` - Create a new version
- `GET /projects/{project_id}/versions/{version_number}` - Get a specific version
- `GET /projects/{project_id}/versions/{version_number}/files` - List all files in a version
- `GET /projects/{project_id}/versions/{version_number}/files/{file_path}` - Get a specific file

### Version Creation

- `POST /projects/{project_id}/versions/{version_number}/files` - Create or update a file
- `POST /projects/{project_id}/versions` - Create a new version from a parent version

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

### Project Structure

```
app/
├── config.py            # Application configuration
├── crud/               # Database operations
│   ├── file.py         # File CRUD operations
│   ├── project.py      # Project CRUD operations
│   └── version/        # Version-related operations
│       ├── crud.py     # Version CRUD
│       ├── file_operations.py  # File manipulation
│       └── template.py # Template handling
├── main.py             # Application entry point
├── models/             # SQLAlchemy models
│   ├── base.py         # Base model class
│   ├── file.py         # File model
│   ├── project.py      # Project model
│   └── version.py      # Version model
├── routes/             # API endpoints
│   ├── projects.py     # Project routes
│   └── versions.py     # Version routes
├── schemas/            # Pydantic schemas
│   ├── base.py         # Base schema class
│   ├── common.py       # Shared schemas
│   ├── file.py         # File schemas
│   ├── project.py      # Project schemas
│   └── version.py      # Version schemas
└── services/           # External services
    └── openrouter.py   # OpenRouter AI integration
```

## Database Schema

The service uses three main tables:

1. `projects` - Stores project metadata
2. `versions` - Stores project versions with parent-child relationships
3. `files` - Stores files associated with project versions

## Contributing

1. Ensure all tests pass before submitting changes
2. Follow coding style guidelines in the codebase
3. Add tests for new features to maintain coverage
4. Update documentation when making significant changes

## License

[Specify license information]