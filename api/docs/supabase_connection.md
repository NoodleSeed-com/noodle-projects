# Supabase Connection Guide

This document describes how to connect to Supabase using the official supabase-py client.

## Overview

We've migrated to using the official supabase-py client instead of custom REST implementation or direct database connections. This provides:

1. Better reliability and compatibility with Supabase's features
2. Simplified synchronous code (removing async/await complexity)
3. Standard patterns that follow Supabase's official documentation
4. Improved maintainability as the client is maintained by Supabase

## Installation

```bash
pip install supabase
```

This is included in the project's requirements.txt file.

## Configuration

The connection is configured using environment variables:

```bash
# .env file
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

You must set these environment variables before running the application. Without them, the Supabase client will raise an error.

## Usage

The application uses a singleton pattern to maintain a single Supabase client instance:

```python
from app.services.supabase.client import get_supabase_client, SupabaseService

# Get the raw client (if needed)
client = get_supabase_client()

# Or use the service for higher-level operations
service = SupabaseService()
projects = service.list_projects()
```

## Key Operations

### Database Operations

The official client provides a PostgreSQL-like query interface:

```python
# Example: Query projects table
projects = client.table("projects").select("*").execute()

# Example: Insert a record
client.table("projects").insert({"name": "New Project", "description": "Test"}).execute()

# Example: Update a record
client.table("projects").update({"name": "Updated Name"}).eq("id", project_id).execute()
```

### File Storage

For file storage operations:

```python
# Upload a file
with open("path/to/file", "rb") as f:
    client.storage.from_("bucket_name").upload("file_name.txt", f)

# Download a file
data = client.storage.from_("bucket_name").download("file_name.txt")
```

## Testing

You can test your Supabase connection with:

```bash
PYTHONPATH=. python api/test_supabase_official.py
```

This script:
1. Creates a test project
2. Adds a version and file
3. Verifies retrieval works correctly
4. Cleans up after itself

## MCP Integration

Our MCP server has been updated to use the synchronous Supabase client:

```bash
PYTHONPATH=. mcp dev api/app/mcp_server_supabase.py
```

## Troubleshooting

If you encounter issues:

1. **Authentication errors**: Verify your SUPABASE_URL and SUPABASE_KEY are correct
2. **Connection timeouts**: Check network connectivity and Supabase status
3. **Database errors**: Ensure table structure matches what the application expects

## Finding Connection Details

You can find your connection details in:
- Supabase Dashboard → Project Settings → API
- Look for "Project URL" and "service_role key"