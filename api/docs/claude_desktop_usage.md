# Using Noodle Projects API with Claude Desktop

This guide explains how to use the Noodle Projects API with Claude Desktop.

## Setup

1. **Start the MCP server**

   Open a terminal and run:
   ```bash
   cd api
   PYTHONPATH=. mcp dev app/mcp_server_rest.py
   ```

   You should see a message saying the MCP Inspector is running at http://localhost:5173.

2. **Connect Claude Desktop to the MCP server**

   In Claude Desktop, enter the following command:
   ```
   /mcp http://localhost:5173
   ```

   Claude should respond with a confirmation that it's connected to the MCP server.

## Managing Projects

### Listing Projects

```
/mcp list_projects
```

Optional parameters:
- `limit`: Maximum number of projects to return (default: 100)
- `offset`: Number of projects to skip (for pagination)
- `include_inactive`: Set to "true" to include inactive/deleted projects

### Creating a Project

```
/mcp create_project name="My New Project" description="This is a new project created via Claude Desktop"
```

Required parameters:
- `name`: The name of the project

Optional parameters:
- `description`: A description of the project

### Getting Project Details

```
/mcp get_project project_id="project-uuid-here"
```

Required parameters:
- `project_id`: The UUID of the project

### Updating a Project

```
/mcp update_project project_id="project-uuid-here" name="Updated Project Name" description="Updated description"
```

Required parameters:
- `project_id`: The UUID of the project

Optional parameters:
- `name`: The new name for the project
- `description`: The new description for the project

### Deleting a Project

```
/mcp delete_project project_id="project-uuid-here"
```

Required parameters:
- `project_id`: The UUID of the project

Note: This performs a soft delete (sets active=false), not a permanent deletion.

## Managing Versions

### Listing Versions

```
/mcp list_versions project_id="project-uuid-here"
```

Required parameters:
- `project_id`: The UUID of the project

Optional parameters:
- `limit`: Maximum number of versions to return (default: 100)
- `offset`: Number of versions to skip (for pagination)

### Creating a Version

```
/mcp create_version project_id="project-uuid-here" name="Version 1" parent_id="parent-version-uuid"
```

Required parameters:
- `project_id`: The UUID of the project
- `name`: The name of the version

Optional parameters:
- `parent_id`: The UUID of the parent version (if this is a child version)

### Getting Version Details

```
/mcp get_version version_id="version-uuid-here"
```

Required parameters:
- `version_id`: The UUID of the version

## Managing Files

### Getting a File

```
/mcp get_file version_id="version-uuid-here" path="src/App.tsx"
```

Required parameters:
- `version_id`: The UUID of the version
- `path`: The file path within the version

### Creating or Updating a File

```
/mcp create_or_update_file version_id="version-uuid-here" path="src/NewFile.tsx" content="console.log('Hello from Claude Desktop!');"
```

Required parameters:
- `version_id`: The UUID of the version
- `path`: The file path within the version
- `content`: The content of the file

## System Status

### Checking MCP Server Health

```
/mcp check_health
```

This command returns the status of the MCP server and its connected services.

## Tips for Using Claude with MCP

1. **Chain commands for complex workflows**:
   You can ask Claude to help you build a workflow by chaining multiple MCP commands. For example:
   
   "Please create a new project, then create an initial version, and add a file to that version."

2. **Use Claude to analyze results**:
   After running an MCP command, ask Claude to explain or analyze the results.

3. **Generate code before creating files**:
   Ask Claude to generate code first, review it, and then use the create_or_update_file command to save it.

4. **Remember UUIDs**:
   Since you'll be working with UUIDs for projects and versions, ask Claude to keep track of them during your session.