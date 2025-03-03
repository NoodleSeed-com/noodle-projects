# Setting Up Claude Desktop with Noodle Projects MCP

This guide explains how to configure Claude Desktop to use the Noodle Projects MCP server.

## Option 1: Manual Configuration

1. First, ensure you have Claude Desktop installed.

2. Locate or create the Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3. Add the following configuration to your `claude_desktop_config.json` file (modify paths as needed):

```json
{
  "mcpServers": {
    "noodle-projects": {
      "command": "mcp",
      "args": ["run", "/path/to/noodle-projects/api/app/mcp_server_rest.py"],
      "env": {
        "PYTHONPATH": "/path/to/noodle-projects",
        "SUPABASE_URL": "https://jsanjojgtyyfpnfqwhgx.supabase.co",
        "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM"
      }
    }
  }
}
```

4. Replace `/path/to/noodle-projects` with the actual path to your project directory.

5. Save the configuration file and restart Claude Desktop.

## Option 2: Configure via Claude Desktop UI

1. Open Claude Desktop.

2. Access Settings by clicking on the menu button (top right) and selecting "Settings".

3. Navigate to the "Developer" tab.

4. Click on "Edit Config". This will open the configuration file in your default text editor.

5. Add the same configuration as shown in Option 1.

6. Save the file and restart Claude Desktop.

## Using the MCP Server

Once configured, you can use the MCP server with Claude Desktop:

1. Open Claude Desktop and start a new conversation.

2. Type `/mcp noodle-projects` to activate the preconfigured MCP server.

3. Claude should indicate that it's connected to the MCP server.

4. Now you can use MCP commands. Examples:
   ```
   /mcp list_projects
   /mcp create_project name="My New Project" description="Created with Claude Desktop"
   ```

## Available MCP Functions

- `check_health` - Check server health
- `list_projects` - List all projects
- `get_project` - Get project details by ID 
- `create_project` - Create a new project
- `update_project` - Update project details
- `delete_project` - Delete a project (soft delete)
- `list_versions` - List versions for a project
- `get_version` - Get version details
- `create_version` - Create a new version
- `get_file` - Get file contents
- `create_or_update_file` - Create or update a file

For more detailed information on using these functions, see the `claude_desktop_usage.md` document.