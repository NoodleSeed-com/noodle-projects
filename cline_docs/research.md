# Research Findings

## FastAPI Best Practices

### Pydantic v2 Models
Research via Perplexity AI revealed current best practices:

1. Model Configuration
   - Use `model_config` with `ConfigDict` instead of `Config` class
   - Enable `from_attributes=True` for ORM compatibility
   - Add JSON schema examples for better documentation

2. Field Validation
   - Use `Field()` for validation and metadata
   - Provide descriptions for OpenAPI documentation
   - Set appropriate default values

3. Model Structure
   - Create base models for shared attributes
   - Use inheritance for request/response models
   - Implement proper validation rules

Example Implementation:
```python
class ProjectBase(BaseModel):
    """Base model for project data"""
    name: str = Field(..., description="The name of the project")
    description: str = Field("", description="Project description")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "My Project",
                "description": "A sample project description"
            }
        }
    )
```

## Database Design Decisions

### Version Management
Research findings on version control patterns:

1. Version Numbering
   - Sequential within project scope
   - Tracked at project level
   - No gaps in numbering
   - Parent-child relationships

2. Storage Strategy
   - Files linked to specific versions
   - No direct file manipulation
   - Path uniqueness per version
   - Content stored as text

### Indexing Strategy
Based on common query patterns:

1. Primary Lookups
   - Project by ID
   - Version by project and number
   - Files by version and path

2. Performance Optimization
   - Composite index on version lookup
   - Index on foreign keys
   - Unique constraints as indexes

## API Design Patterns

### RESTful Best Practices
Research on modern API design:

1. Resource Naming
   - Noun-based endpoints
   - Clear hierarchy
   - Consistent patterns
   - Version in path

2. Status Codes
   - 200: Successful operations
   - 201: Resource creation
   - 404: Not found
   - 400: Validation errors

3. Query Parameters
   - Pagination with skip/limit
   - Optional filtering
   - Default values
   - Parameter validation

## Implementation Insights

### Error Handling
Best practices for API errors:

1. Exception Types
   - HTTP exceptions
   - Database errors
   - Validation errors
   - Custom errors

2. Response Format
   - Consistent structure
   - Clear messages
   - Proper status codes
   - Additional context

## OpenRouter Integration with Gemini

### Response Format Validation
Research findings from Gemini 2.0 Flash testing:

1. Response Structure
   - Responses consistently wrapped in `<noodle_response>` tags
   - Valid JSON structure within tags
   - Proper escaping of code content
   ```json
   <noodle_response>
   {"changes": [{
     "operation": "create",
     "path": "src/components/Button.tsx",
     "content": "import React from 'react';\n..."
   }]}
   </noodle_response>
   ```

2. Code Generation Capabilities
   - Accurate TypeScript type definitions
   - Modern React patterns (functional components, hooks)
   - Styled-components implementation
   - Accessibility considerations
   - Proper component exports

3. Model Selection
   - google/gemini-2.0-flash-001 suitable for code generation
   - Fast response times
   - Consistent formatting
   - Follows provided templates

4. Integration Patterns
   - Environment-based configuration
   - Proper error handling
   - Response validation
   - Content parsing
   - Testing considerations

### Key Learnings
1. Response Validation
   - Always verify `<noodle_response>` tags presence
   - Validate JSON structure
   - Check required fields (operation, path, content)
   - Verify operation values (create, update, delete)

2. Error Handling
   - Handle missing API keys gracefully
   - Validate response format
   - Parse JSON safely
   - Provide clear error messages

## Future Research Topics

1. Batch Operations
   - Efficient processing
   - Transaction management
   - Error handling
   - Progress tracking

2. Advanced Querying
   - Search implementation
   - Filter optimization
   - Sort mechanisms
   - Query validation

3. Performance Monitoring
   - Metrics collection
   - Query analysis
   - Resource usage
   - Optimization opportunities

## Service Integration Testing

### OpenRouter Service Testing Issues
Research findings from test implementation:

1. Mocking Challenges
   - Direct service imports make mocking difficult
   - Testing mode returns empty list by default
   - Mock not being called due to import structure

2. Current Implementation
   ```python
   # projects.py
   from app.services.openrouter import openrouter  # Direct import

   # Test
   @pytest.fixture
   def mock_openrouter():
       with patch("app.services.openrouter.openrouter") as mock_service:
           mock_service.get_file_changes.return_value = [...]
   ```

3. Recommended Patterns
   - Use dependency injection for services
   - Avoid direct imports of service instances
   - Make test mode behavior configurable
   - Document mocking requirements

4. Solution Implementation
   - Move service dependency to module level:
     ```python
     # services/openrouter.py
     openrouter = OpenRouterService()
     
     def get_openrouter():
         """Dependency to get OpenRouter service."""
         return openrouter
     ```
   - Use dependency in routes:
     ```python
     # projects.py
     from app.services.openrouter import get_openrouter
     
     @router.post("/versions")
     def create_version(
         openrouter_service = Depends(get_openrouter)
     ):
         changes = openrouter_service.get_file_changes(...)
     ```
   - Override in tests:
     ```python
     # conftest.py
     app.dependency_overrides[get_openrouter] = lambda: mock_openrouter
     ```
   - Verify service calls:
     ```python
     # Instead of assert_called_once_with():
     mock_openrouter.get_file_changes.assert_called_once()
     call_args = mock_openrouter.get_file_changes.call_args[1]
     assert call_args["project_context"] == expected_context
     ```

5. Key Learnings
   - Keep service dependencies centralized in their modules
   - Use consistent import paths for dependencies
   - Clear overrides after tests
   - When testing service calls with complex parameters:
     * Use assert_called_once() to verify the call happened
     * Check individual arguments using call_args[1] for kwargs
     * This is more flexible than assert_called_once_with()
