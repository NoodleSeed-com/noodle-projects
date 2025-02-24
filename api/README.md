# Projects API

A FastAPI microservice for managing projects and their versions.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI) at http://localhost:8000/docs
- Alternative API documentation (ReDoc) at http://localhost:8000/redoc

## API Endpoints

### Projects

- `GET /projects` - List all active projects
- `POST /projects` - Create a new project
- `GET /projects/{project_id}` - Get a specific project
- `PUT /projects/{project_id}` - Update a project
- `DELETE /projects/{project_id}` - Soft delete a project

### Project Versions

- `GET /projects/{project_id}/versions` - List all versions of a project
  - Returns a simplified list of versions with {id, version_number, name}
  - Versions are ordered by version_number
- `GET /projects/{project_id}/versions/{version_number}` - Get a specific version
  - Returns full version details including parent_version (the parent's version number)
  - Maintains parent_version_id for backward compatibility

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
   - `parent_version_id`: UUID (Optional, Foreign Key to versions)
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

## Entity Semantics

The following diagram illustrates the relationships and structure of the system's components:

```mermaid
classDiagram
    %% Base Classes
    class Base {
        <<abstract>>
        +UUID id
        +DateTime created_at
        +DateTime updated_at
    }
    
    class BaseSchema {
        <<abstract>>
        +from_attributes: bool
        +json_schema_extra
    }

    %% Domain Models
    class Project {
        +String name
        +Text description
        +Boolean active
        +List~Version~ versions
        +int latest_version_number() <<computed>>
        note for Project "latest_version_number is a hybrid property that returns the highest version_number from the project's versions, or 0 if no versions exist"
    }
    
    class Version {
        +UUID project_id
        +int version_number
        +UUID parent_version_id
        +String name
        +Project project
        +List~File~ files
        note for Version "- Initial version (0) created with new project
        - Parent-child relationship tracked by parent_version_id internally
        - Parent version number exposed in API responses
        - Version numbers must be unique within a project (DB constraint)
        - Implementation note: Version creation endpoint not implemented"
    }
    
    class File {
        +UUID version_id
        +String path
        +Text content
        +Version version
    }

    %% Pydantic Schemas
    class ProjectBase {
        +String name
        +String description
    }
    
    class ProjectCreate {
    }
    
    class ProjectUpdate {
        +Optional~String~ name
        +Optional~String~ description
        +Optional~Boolean~ active
    }
    
    class ProjectResponse {
        +UUID id
        +int latest_version_number
        +Boolean active
        +DateTime created_at
        +DateTime updated_at
    }

    %% CRUD Operations
    class ProjectCRUD {
        +get(Session, UUID) Project
        +get_multi(Session, int, int) List~Project~
        +create(Session, ProjectCreate) Project
        +update(Session, UUID, ProjectUpdate) Project
        +delete(Session, UUID) Project
        +get_version(Session, UUID, int) Version
        +get_versions(Session, UUID, int, int) List~Version~
    }

    %% API Endpoints
    class ProjectAPI {
        +listProjects() List~ProjectResponse~
        +createProject() ProjectResponse
        +getProject(id) ProjectResponse
        +updateProject(id) ProjectResponse
        +deleteProject(id) ProjectResponse
        +listVersions(id) List~VersionResponse~
        +getVersion(id, number) VersionResponse
    }

    %% Relationships
    Base <|-- Project
    Base <|-- Version
    Base <|-- File
    BaseSchema <|-- ProjectBase
    ProjectBase <|-- ProjectCreate
    ProjectBase <|-- ProjectResponse
    Project "1" --> "*" Version : has
    Version "1" --> "*" File : contains
    ProjectAPI --> ProjectCRUD : uses
    ProjectCRUD --> Project : manages
    ProjectCreate --> Project : creates
    ProjectUpdate --> Project : updates
    Project --> ProjectResponse : returns
```

The diagram shows:
- Base classes (`Base` and `BaseSchema`) that provide common functionality
- Domain models (`Project`, `Version`, `File`) and their relationships
- Pydantic schemas for validation and serialization
- CRUD operations through the `ProjectCRUD` class
- API endpoints that expose the functionality
- Inheritance and association relationships between components
