# Noodle Projects API

A FastAPI microservice for managing versioned React/TypeScript projects with AI-powered code generation capabilities.

## Overview

This service provides a RESTful API for:
- Creating and managing React/TypeScript projects with version control
- File-level version management with parent-child relationships
- React/TypeScript template-based project initialization
- AI-assisted code generation using OpenRouter (Gemini 2.0 Flash)

## Features

- **Project Management**
  - Create, read, update, and delete projects
  - Project-level active state management
  - Soft deletion support

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

- **AI Integration**
  - Code generation using OpenRouter API
  - Structured response format
  - Template-aware suggestions
  - Context-based code modifications

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Supabase CLI
- OpenRouter API key (for Gemini 2.0 Flash integration)
- Node.js and npm (for template projects)

### Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd noodle-projects
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix
   # or
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r api/requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp api/.env.example api/.env
   # Edit api/.env with your configuration
   ```

   Required variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `OPENROUTER_API_KEY`: OpenRouter API key (for AI features)

5. Start Supabase:
   ```bash
   supabase start
   ```

6. Run database migrations:
   ```bash
   supabase db reset
   ```

### Development Server

Start the development server:
```bash
uvicorn api.app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

### API Endpoints

#### Projects
- `GET /api/projects` - List all active projects
- `POST /api/projects` - Create a new project
- `GET /api/projects/{project_id}` - Get project details
- `PUT /api/projects/{project_id}` - Update project
- `DELETE /api/projects/{project_id}` - Soft delete project

#### Versions
- `GET /api/projects/{project_id}/versions` - List project versions
- `POST /api/projects/{project_id}/versions` - Create new version with AI changes
- `GET /api/projects/{project_id}/versions/{version_number}` - Get version details

### Response Formats

#### Project Response
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "latest_version_number": 0,
  "active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Version Response
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "version_number": 0,
  "name": "string",
  "parent_version_id": "uuid",
  "parent_version": 0,
  "created_at": "datetime",
  "updated_at": "datetime",
  "files": [
    {
      "id": "uuid",
      "path": "string",
      "content": "string"
    }
  ],
  "active": true
}
```

Detailed OpenAPI documentation is available at `/api/openapi.json` and Swagger UI at `/docs`.

## Development

### Project Structure
```
/
├── api/                      # FastAPI service
│   ├── app/
│   │   ├── config.py        # App & DB configuration
│   │   ├── main.py          # FastAPI app setup
│   │   ├── projects.py      # API endpoints
│   │   ├── crud.py          # Database operations
│   │   ├── models/          # Database models
│   │   └── services/        # External services
│   │       ├── openrouter.py  # AI integration
│   │       └── prompts/     # AI prompts
│   ├── templates/           # Project templates
│   │   └── version-0/       # React/TypeScript template
│   │       ├── src/         # React source code
│   │       ├── public/      # Static assets
│   │       ├── package.json
│   │       └── tsconfig.json
│   └── tests/               # Test suite
├── supabase/                # Database configuration
└── cline_docs/             # Documentation
```

### Version Control Features

#### Version 0 Template
- Every new project starts with version 0
- Based on React/TypeScript template
- Includes basic React setup with TypeScript configuration
- Template structure preserved exactly during initialization

#### Version Management
- Versions are numbered sequentially starting from 0
- Each version can have a parent version
- Version numbers must be unique within a project
- Negative version numbers are rejected
- Files are immutable within a version

#### File Management
- Files are always associated with specific versions
- File paths must be unique within a version
- Empty file paths are rejected
- Paths must be relative to project root
- Files are eagerly loaded with versions

### Testing

The test suite covers:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api/app api/tests/ -v

# Test Categories
pytest api/tests/test_main.py -v                # Main app tests
pytest api/tests/test_projects/test_crud.py -v  # CRUD operations
pytest api/tests/test_projects/test_validation.py -v  # Input validation
pytest api/tests/test_projects/test_versions.py -v    # Version management
pytest api/tests/test_projects/test_files.py -v      # File handling
pytest api/tests/test_projects/test_edge_cases.py -v # Edge cases
pytest api/tests/test_projects/test_openrouter.py -v # AI integration
```

Test coverage requirements:
- Minimum 80% overall coverage
- 100% coverage for models
- 100% coverage for critical paths

### Development Standards

#### Code Style
- FastAPI and Pydantic v2 best practices
- PEP 8 guidelines
- Type hints throughout
- Comprehensive docstrings
- Clear error messages

#### API Design
- RESTful endpoints
- Clear resource hierarchy
- Consistent response formats
- Proper status code usage
- Dependency injection pattern

#### Database Operations
- Connection pooling
- Transaction management
- Row Level Security enabled
- Soft deletion through active flag
- Proper indexing and constraints

## Database Schema

### Key Tables
- projects: Project metadata and active state
- versions: Version control and relationships
- files: Version-specific file content

### Relationships
- Project -> Version: One-to-Many
- Version -> File: One-to-Many

### Security

#### Access Control
- Row Level Security enabled at database level
- Project-level active state management
- State inheritance in versions
- Input validation at multiple layers

#### Environment Configuration
- Environment-based settings
- Secure credential management
- Test mode configuration
- OpenRouter API key management

### AI Integration

#### OpenRouter Service
- Uses Gemini 2.0 Flash model
- Structured response format with noodle_response tags
- File change validation
- Duplicate path detection
- Error handling with clear messages

#### Change Operations
- Create new files
- Update existing files
- Delete files
- Path uniqueness validation
- Content validation

### Error Handling

#### API Errors
- 404: Resource not found
- 403: Operation not allowed (e.g., modifying inactive project)
- 422: Validation error
- 500: Internal server error

#### Database Constraints
- Unique version numbers per project
- Unique file paths within versions
- Non-negative version numbers
- Non-empty file paths

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[License Information]
