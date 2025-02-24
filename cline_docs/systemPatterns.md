# System Patterns

## Project State Management

### Active State Inheritance
1. Project Level:
   - Single source of truth for active state
   - Boolean active flag in projects table
   - Default value: true
   - Soft deletion sets active=false
   - Reactivation allowed through update endpoint

2. State Inheritance:
   - Versions inherit active state from project
   - No independent version activation
   - Files accessed through version context only
   - No direct file-level operations

3. Operation Rules:
   - Write operations blocked on inactive projects:
     * Creating new versions
     * Modifying project details
     * Any file operations
   - Read operations allowed but show inactive state
   - Reactivation only through project update endpoint
   - State changes cascade through relationships

4. Implementation Requirements:
   - Check project.active before write operations
   - Return 403 Forbidden for writes to inactive projects
   - Include active state in version responses
   - Maintain single source of truth pattern

### Version Listing Behavior
1. Active Projects:
   - List all versions ordered by version number
   - Include essential version metadata:
     * id: UUID
     * version_number: Sequential number
     * name: Version name
   - Support pagination parameters

2. Inactive Projects:
   - Return empty version list
   - Maintain consistent response structure
   - No error response needed

3. Version Response Patterns:
   - Detailed version responses include active state
   - List responses exclude active state (inherited)
   - Files included only in detailed responses

## API Design Patterns

### HTTP Methods
1. Supported Operations:
   - GET: Read operations
   - POST: Create operations
   - PUT: Update operations
   - DELETE: Soft deletion
   
2. Unsupported Operations:
   - PATCH: Not implemented
   - Direct file operations: Handled through versions

### Response Patterns
1. Success Responses:
   - 200: Successful operations
   - 201: Resource creation

2. Error Responses:
   - 403: Operations on inactive projects
   - 404: Resource not found
   - 422: Invalid input validation

### Validation Patterns
1. Project State:
   - Validate active state before write operations
   - Allow reactivation regardless of state
   - Block other modifications when inactive

2. Version Operations:
   - Validate parent version exists
   - Check project active state
   - Validate file operations within version context

## File Management

### File Operations
1. Version-Centric:
   - Files belong to specific versions
   - No direct file endpoints
   - Changes create new versions
   - Files immutable within versions

2. File Validation:
   - Path uniqueness within version
   - Non-empty path requirement
   - Content validation
   - Path format validation

### Version Creation
1. Process:
   - Copy parent version files
   - Apply requested changes
   - Create new version number
   - Store complete file set

2. Change Types:
   - Create: Add new file
   - Update: Modify existing file
   - Delete: Remove file from version

## Testing Patterns

### State Testing
1. Project State:
   - Test active/inactive transitions
   - Verify operation restrictions
   - Check state inheritance
   - Validate reactivation

2. Version Testing:
   - Test version listing behavior
   - Verify state inheritance
   - Check operation restrictions
   - Test pagination

### Response Testing
1. Schema Validation:
   - Verify response formats
   - Check required fields
   - Validate type constraints
   - Test optional fields

2. Error Handling:
   - Test invalid operations
   - Verify error messages
   - Check status codes
   - Validate error formats

## Error Handling Patterns

### Service Layer Errors
1. OpenRouter Service:
   - Validate file paths before processing
   - Check for duplicate paths in changes
   - Raise ValueError for validation failures
   - Maintain consistent error messages

2. Error Propagation:
   - Catch service errors at API layer
   - Convert to appropriate HTTP status codes:
     * ValueError -> 400 Bad Request
     * IntegrityError -> 409 Conflict
     * OperationalError -> 503 Service Unavailable
   - Maintain transaction integrity
   - Roll back on failure

### Transaction Management
1. Rollback Patterns:
   - Roll back on validation errors
   - No partial state persistence
   - Maintain database consistency
   - Clear error reporting

2. Edge Case Handling:
   - Handle duplicate paths
   - Validate file operations
   - Check version constraints
   - Maintain referential integrity

### Testing Strategy
1. Error Scenarios:
   - Test validation failures
   - Verify error propagation
   - Check transaction rollback
   - Validate error responses

2. Mock Integration:
   - Use FastAPI dependency overrides
   - Mock service responses
   - Simulate error conditions
   - Verify error handling flow
