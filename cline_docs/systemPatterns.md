# System Patterns

## API Response Patterns

### Version Response Pattern
The system uses a consistent pattern for version responses that includes associated files:

1. Detailed Version Response:
   - Used for single version retrieval
   - Includes complete file information
   - Maintains parent-child relationships
   - Example endpoint: GET /api/projects/{id}/versions/{number}

2. List Version Response:
   - Used for version listing
   - Simplified format without files
   - Only includes essential identifying information
   - Example endpoint: GET /api/projects/{id}/versions

### File Handling Pattern

1. File Storage:
   - Files are immutable per version
   - Each file belongs to exactly one version
   - Files are stored with:
     * Unique UUID
     * Relative path
     * Content
     * Version association

2. Loading Strategy:
   - Eager loading with versions
   - Prevents N+1 query problems
   - Uses SQLAlchemy joinedload

3. Response Transformation:
   - SQLAlchemy models converted to Pydantic DTOs
   - Maintains clean separation of concerns
   - Ensures type safety

## Database Patterns

### Entity Relationships

1. Project -> Version:
   - One-to-Many relationship
   - Soft deletion at project level
   - Versions maintain project history
   - Unique version numbers per project

2. Version -> File:
   - One-to-Many relationship
   - Hard deletion with version (cascade)
   - Files are version-specific
   - No cross-version file sharing

### Version Numbering

1. Initial Version:
   - Automatically created with new projects
   - Always version number 0
   - Named "Initial Version"

2. Version Sequence:
   - Monotonically increasing per project
   - Unique within each project
   - No gaps required
   - No negative numbers allowed

## Implementation Patterns

### Response Transformation

1. DTO Pattern:
   ```python
   # Convert SQLAlchemy models to DTOs
   return ProjectVersionResponse(
       id=version.id,
       project_id=version.project_id,
       version_number=version.version_number,
       name=version.name,
       files=[FileResponse(...) for file in version.files]
   )
   ```

2. Eager Loading Pattern:
   ```python
   # Prevent N+1 queries by eager loading relationships
   select(ProjectVersion).options(
       joinedload(ProjectVersion.files)
   ).filter(...)
   ```

3. List Response Pattern:
   ```python
   # Simplified response for lists
   return [ProjectVersionListItem(
       id=id,
       version_number=number,
       name=name
   ) for id, number, name in result]
   ```

### Testing Patterns

1. Test Organization:
   ```
   api/tests/
   └── test_projects/
       ├── conftest.py         # Shared fixtures and DB setup
       ├── test_crud.py        # Basic CRUD operations
       ├── test_validation.py  # Input validation
       ├── test_versions.py    # Version management
       └── test_files.py       # File handling
   ```

2. Test Categories:
   - CRUD Tests: Basic create, read, update, delete operations
   - Validation Tests: Input validation and constraints
   - Version Tests: Version management and relationships
   - File Tests: File handling and response formats

3. Fixture Organization:
   ```python
   # Shared fixtures in conftest.py
   @pytest.fixture
   def test_files():
       return [
           {
               "path": "src/main.py",
               "content": "print('Hello, World!')"
           },
           {
               "path": "README.md",
               "content": "# Test Project"
           }
       ]
   ```

4. Test Patterns by Category:
   - CRUD: Test basic operations and response formats
   - Validation: Test constraints and error cases
   - Versions: Test relationships and numbering
   - Files: Test content and structure

## Best Practices

1. File Handling:
   - Always use relative paths
   - Validate file content
   - Maintain immutability per version
   - Use eager loading for efficiency

2. Response Structure:
   - Keep DTOs separate from DB models
   - Use consistent response formats
   - Include complete object graphs
   - Document all fields

3. Database Operations:
   - Use appropriate indexes
   - Implement proper constraints
   - Maintain referential integrity
   - Optimize query patterns
