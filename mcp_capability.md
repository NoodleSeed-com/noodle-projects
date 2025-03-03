# Adding MCP Capability to Existing REST Microservices

This document outlines a methodical approach for adding Model Context Protocol (MCP) capabilities to an existing REST-based microservice without disrupting its original functionality.

## Overview

The Model Context Protocol (MCP) allows Claude and other AI assistants to directly access services through a standardized interface. By adding MCP capability to an existing REST microservice, you can:

1. Maintain existing REST API functionality for traditional clients
2. Enable AI assistants to directly access your service's features
3. Reuse business logic between both interfaces
4. Avoid duplicating code or maintaining separate services

## Implementation Strategy

This guide follows a "share the core, change the interface" approach where:
- Business logic, models, and database connections are shared
- Only the interface layer is different between REST and MCP

### Step 1: Add MCP SDK Dependency

```bash
# Add to requirements.txt
mcp>=1.2.0
pip install -r requirements.txt
```

### Step 2: Create MCP Server Module

Create a new file (e.g., `app/mcp_server.py`) that imports your existing business logic:

```python
from mcp.server.fastmcp import FastMCP
import logging
from uuid import UUID
from typing import Optional, Dict, Any

# Import existing business logic
from app.api.memory import (
    create_memory as api_create_memory,
    get_memory as api_get_memory,
    update_memory as api_update_memory,
    get_supabase
)
from app.models.memory import MemoryUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server - simple name for local use
mcp = FastMCP("ServiceName")

# Define MCP tools that wrap existing business logic
@mcp.tool()
async def example_tool(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """Tool description with clear documentation.
    
    Args:
        param1: Description of parameter
        param2: Optional parameter description
    
    Returns:
        Response with operation results
    """
    try:
        # Reuse existing business logic
        result = await your_existing_function(param1, param2)
        
        # Transform result for MCP response format if needed
        return {
            "key1": result.value1,
            "key2": result.value2
        }
    except Exception as e:
        logger.error(f"Error in example_tool: {e}")
        return {"error": str(e)}

# Add main block to allow direct execution
if __name__ == "__main__":
    mcp.run()
```

### Step 3: Create Testing Utilities

Create a test script to validate that the MCP server can run correctly:

```python
#!/usr/bin/env python
"""
Test the MCP server locally by running 'mcp inspect' command.
"""
import subprocess
import sys
import os

def test_mcp_server():
    """Test the MCP server by running the MCP inspect command."""
    print("Testing MCP server...")
    
    try:
        # Run mcp command to validate the server
        result = subprocess.run(
            ["mcp", "run", "app/mcp_server.py"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        print(f"Output: {result.stdout}")
        print(f"Errors: {result.stderr}")
        
        # Check if we got a successful response
        if result.returncode == 0:
            print("✅ MCP server is configured correctly!")
            return True
        else:
            print("❌ MCP server validation failed.")
            return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

if __name__ == "__main__":
    test_mcp_server()
```

### Step 4: Update Documentation

Update project documentation in README.md and other docs to reflect MCP capability:

```markdown
## MCP Server Commands
- Run MCP server in development mode: `PYTHONPATH=. mcp dev app/mcp_server.py`
- Test MCP server locally: `PYTHONPATH=. python test_mcp_local.py`
- Use with Claude: Add server through Claude Desktop settings
```

### Step 5: Configure Claude Desktop

Configure Claude Desktop to use your MCP server:

1. Locate the Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add your MCP server to the configuration:

```json
{
  "mcpServers": {
    "YourServiceName": {
      "command": "/path/to/python",
      "args": [
        "-m",
        "mcp.run",
        "/path/to/your/app/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/your/project",
        "YOUR_ENV_VAR1": "value1",
        "YOUR_ENV_VAR2": "value2"
      },
      "disabled": false,
      "autoApprove": [
        "tool_name1",
        "tool_name2"
      ]
    }
  }
}
```

## Conversion Patterns

### REST Endpoint to MCP Tool

| REST API Pattern | MCP Equivalent |
|------------------|---------------|
| `GET /resource/{id}` | `@mcp.tool() async def get_resource(id: str)`|
| `POST /resource` | `@mcp.tool() async def create_resource(params)`|
| `PUT /resource/{id}` | `@mcp.tool() async def update_resource(id, params)`|
| `DELETE /resource/{id}` | `@mcp.tool() async def delete_resource(id)`|

### Error Handling

For consistent error handling between REST and MCP:

```python
# REST error handling
@router.get("/endpoint")
async def endpoint():
    try:
        result = business_logic_function()
        return SuccessResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MCP error handling
@mcp.tool()
async def mcp_tool():
    try:
        result = business_logic_function()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"success": False, "error": str(e)}
```

## Testing Methodology

1. **Unit Testing**: Test individual tool functions with mocked database
2. **Integration Testing**: Test full business logic flow
3. **Local Testing**: Use `mcp dev` to test with the MCP Inspector
4. **Claude Testing**: Test with Claude Desktop for end-to-end verification

## Best Practices

1. **Keep Business Logic Separate**: Never duplicate business logic between REST and MCP interfaces
2. **Consistent Response Formats**: Design consistent response structures
3. **Thorough Documentation**: Document all tools with clear descriptions and parameter specifications
4. **Error Handling**: Include comprehensive error handling in all tools
5. **Tool Naming**: Use clear, action-oriented names for tools (get_X, create_X, update_X)
6. **Parameter Validation**: Use type hints and validation for all parameters
7. **Environment Variables**: Properly handle environment variables for configuration

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Ensure PYTHONPATH includes your project root |
| Authentication failures | Verify all credentials and API keys in the Claude Desktop config |
| Tool not found | Check correct naming and registration of tools |
| Database connection issues | Verify database credentials and connection settings |

## Example: Converting CRUD Operations

```python
# REST API version
@router.post("/create")
async def create_item(item: ItemCreate):
    return await business_logic.create_item(item)

# MCP version
@mcp.tool()
async def create_item(name: str, description: str, tags: Optional[List[str]] = None):
    """Create a new item.
    
    Args:
        name: Item name
        description: Item description
        tags: Optional list of tags
        
    Returns:
        Created item information
    """
    item = ItemCreate(name=name, description=description, tags=tags or [])
    result = await business_logic.create_item(item)
    return result.dict()
```

This approach ensures both REST and MCP interfaces use the same underlying business logic while providing appropriate interfaces for their respective clients.