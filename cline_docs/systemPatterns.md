# System Patterns

## Validation Patterns

### Project Model Validation
- Project names must be non-empty (enforced via Pydantic constr(min_length=1))
- Description is optional with default empty string
- Version numbers must be non-negative (enforced via database CHECK constraint)
- File paths must be non-empty and unique within a version

### Integration Test Patterns
- Test both API endpoints and direct CRUD operations
- Verify template initialization in version 0
- Validate input constraints at API level
- Test file path uniqueness and content matching
- Mock external services (e.g., OpenRouter) for version creation

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
     * Relative path (non-empty, unique per version)
     * Content
     * Version association

2. File Validation:
   - Application-level validation:
     * Empty paths rejected with ValueError
     * Validation occurs in File model __init__
     * Prevents invalid data from reaching database
   - Database-level constraints:
     * Unique constraint on (project_version_id, path)
     * Check constraint ensures non-empty paths
     * Provides additional safety layer

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
   - Created from version-0 template directory
   - Template Structure:
     ```
     api/templates/version-0/
     ├── src/
     │   ├── index.tsx           # React entry point
     │   ├── App.tsx            # Main App component
     │   └── components/
     │       └── HelloWorld.tsx # Example component
     ├── public/
     │   └── index.html         # HTML template
     ├── tsconfig.json          # TypeScript configuration
     └── package.json          # Project dependencies
     ```
   - Ensures consistent starting point for all projects
   - Provides complete TypeScript React project structure

2. Version Sequence:
   - Monotonically increasing per project
   - Unique within each project
   - No gaps required
   - No negative numbers allowed

3. Version Validation:
   - Multi-layer validation approach:
     * Model-level validation in __init__: Raises IntegrityError for negative numbers
     * Database constraint: CHECK version_number >= 0
     * API-level validation: Path parameter validation for version endpoints
   - Early validation prevents invalid data from reaching database
   - Consistent error handling across layers

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

### CORS Pattern
- Allow all origins in development with ["*"]
- FastAPI CORSMiddleware behavior:
  * When allow_origins=["*"], origin is reflected back
  * Response includes actual requesting origin in access-control-allow-origin
  * Maintains security while allowing flexible development
  * Example: Request from "http://localhost" gets "http://localhost" in response header

### Testing Patterns

1. Test Organization:
   ```
   api/tests/
   └── test_projects/
       ├── conftest.py         # Shared fixtures and DB setup
       ├── test_crud.py        # Basic CRUD operations
       ├── test_validation.py  # Input validation
       ├── test_versions.py    # Version management
       ├── test_files.py       # File handling
       └── test_edge_cases.py  # Edge cases and constraints
   ```

2. Test Categories:
   - Integration Tests: End-to-end API flow testing
   - CRUD Tests: Basic create, read, update, delete operations
   - Validation Tests: Input validation and constraints
   - Version Tests: Version management and relationships
   - File Tests: File handling and response formats
   - Edge Cases: Boundary conditions and error scenarios

3. Critical Integration Test Pattern:
   ```python
   def test_create_project_with_version_0(client):
       """Core integration test that verifies project creation flow."""
       # 1. Create project via API
       response = client.post("/api/projects/", json={
           "name": "Test Project",
           "description": "Test Description"
       })
       assert response.status_code == 201
       project = response.json()
       
       # 2. Verify version 0 through API
       response = client.get(f"/api/projects/{project['id']}/versions/0")
       assert response.status_code == 200
       version_0 = response.json()
       
       # 3. Validate template files
       expected_files = get_template_files()
       actual_files = {f["path"]: f["content"] for f in version_0["files"]}
       assert set(actual_files.keys()) == set(expected_files.keys())
   ```
   
   This pattern tests:
   - Complete API flow from project creation to version retrieval
   - Automatic version 0 creation with template files
   - Response structure and status codes
   - Database integration
   - File handling system

4. Fixture Organization:
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

5. Test Patterns by Category:
   - CRUD: Test basic operations and response formats
   - Validation: Test constraints and error cases
   - Versions: Test relationships and numbering
   - Files: Test content and structure
   - Edge Cases: Test boundary conditions and error handling

6. Validation Testing Pattern:
   ```python
   # Test model-level validation
   with pytest.raises(IntegrityError, match="Version number cannot be negative"):
       ProjectVersion(version_number=-1, ...)

   # Test database constraints
   with pytest.raises(IntegrityError):
       # Attempt to violate unique constraint
       test_db.add(duplicate_version)
       test_db.commit()
   ```

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

4. Validation Strategy:
   - Implement validation at multiple layers
   - Use model-level validation for early error catching
   - Add database constraints as safety net
   - Provide clear error messages
   - Handle edge cases explicitly

## Service Integration Patterns

### OpenRouter Service Patterns

1. Prompt Management:
   - Separate files for system and user prompts
   - Located in services/prompts directory:
     ```
     api/app/services/prompts/
     ├── system_message.md    # AI role and response format
     └── user_message_template.md  # Request template
     ```
   - Allows easy maintenance and updates
   - Keeps prompts version controlled

2. Response Format:
   ```json
   <noodle_response>
   {
     "changes": [{
       "operation": "create|update|delete",
       "path": "relative/file/path",
       "content": "file content"
     }]
   }
   </noodle_response>
   ```

3. Model Configuration:
   ```python
   # models/project.py
   class FileChange(BaseModel):
       operation: Literal["create", "update", "delete"]
       path: str
       content: str

   class AIResponse(BaseModel):
       changes: List[FileChange]
   ```

4. Validation Layers:
   a. Response Format Validation:
      ```python
      # Extract and validate response tags
      match = re.search(r"<noodle_response>\s*(.*?)\s*</noodle_response>", 
                       response_text, re.DOTALL)
      if not match:
          raise ValueError("AI response missing noodle_response tags")
      ```

   b. JSON Structure Validation:
      ```python
      # Parse and validate with Pydantic
      ai_response = AIResponse.model_validate_json(match.group(1))
      ```

   c. File Path Validation:
      ```python
      # Check for duplicate paths
      paths = [change.path for change in ai_response.changes]
      if len(paths) != len(set(paths)):
          raise ValueError("Duplicate file paths found in changes")
      ```

5. Error Handling:
   a. Network Errors:
      - OpenAIError: General API errors
      - APITimeoutError: Request timeouts
      - RateLimitError: Rate limit exceeded

   b. Response Errors:
      - ValueError: Missing tags, invalid JSON, duplicate paths
      - AttributeError: Missing required attributes
      - IndexError: Empty response

   c. Testing Pattern:
      ```python
      def test_error_handling():
          # Test rate limit
          mock_response = MagicMock(status_code=429)
          error_body = {
              "error": {
                  "message": "Rate limit exceeded",
                  "type": "requests",
                  "code": "rate_limit_exceeded"
              }
          }
          mock_client.create.side_effect = RateLimitError(
              message="Rate limit exceeded",
              response=mock_response,
              body=error_body
          )
      ```

6. Model Selection:
   ```python
   completion = client.chat.completions.create(
       model="google/gemini-2.0-flash-001",
       messages=[
           {
               "role": "system",
               "content": system_message
           },
           {
               "role": "user",
               "content": user_message
           }
       ]
   )
   ```

7. Testing Strategy:
   a. Test Categories:
      - Basic functionality (testing mode, API key)
      - Response validation (missing tags, invalid JSON)
      - Error handling (API errors, timeouts, rate limits)
      - Edge cases (empty inputs, special characters)
      - File validation (duplicates, nested paths)

   b. Mock Patterns:
      ```python
      # Mock service for testing
      @pytest.fixture
      def mock_openrouter():
          with patch('app.services.openrouter.OpenRouterService._get_client') as mock:
              mock_client = MagicMock()
              mock.return_value = mock_client
              yield mock_client
      ```

   c. Environment Handling:
      ```python
      # Test environment setup
      monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
      monkeypatch.setenv("TESTING", "false")
      ```

### Dependency Injection
1. Service Definition:
   ```python
   # services/openrouter.py
   openrouter = OpenRouterService()
   
   def get_openrouter():
       """Dependency to get OpenRouter service."""
       return openrouter
   ```

2. Service Usage:
   ```python
   # routes/projects.py
   from app.services.openrouter import get_openrouter
   
   @router.post("/versions")
   def create_version(
       openrouter_service = Depends(get_openrouter)
   ):
       changes = openrouter_service.get_file_changes(...)
   ```

3. Testing Pattern:
   ```python
   # conftest.py
   @pytest.fixture
   def client(mock_openrouter):
       app.dependency_overrides[get_openrouter] = lambda: mock_openrouter
       yield TestClient(app)
       app.dependency_overrides.clear()
   ```

4. Service Call Verification:
   ```python
   # test_versions.py
   def test_service_call(mock_service):
       # Verify call happened
       mock_service.method.assert_called_once()
       
       # Check specific arguments
       call_args = mock_service.method.call_args[1]
       assert call_args["param1"] == expected_value
       
       # Verify complex parameters
       assert len(call_args["items"]) > 0
   ```

5. Best Practices:
   - Keep service dependencies in their modules
   - Use consistent import paths
   - Clear dependency overrides after tests
   - Verify service calls with flexible assertions
   - Include context in service calls (e.g., current files)
