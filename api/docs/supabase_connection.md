# Supabase Connection Guide

This document describes options for connecting to the Supabase PostgreSQL database in this project.

## Connection Methods

There are two primary methods for connecting to Supabase:

1. **Direct Database Connection** (using SQLAlchemy/asyncpg)
2. **REST API Connection** (preferred for reliability)

## Connection Types

Supabase offers three connection modes:

1. **Direct Connection**:
   - Best for long-running applications
   - Requires IPv6 support
   - Format: `postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres?sslmode=require`

2. **Supavisor Session Mode**:
   - For persistent servers when IPv6 isn't supported
   - Format: `postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require`

3. **Supavisor Transaction Mode** (recommended for our application):
   - Best for serverless functions and ephemeral environments
   - Provides connection pooling
   - Format: `postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?ssl=true&prepared_statement_cache_size=0`
   - Note: Notice port 6543 instead of 5432

## Current Configuration

We use **Transaction Mode** for optimal performance with short-lived connections. Transaction mode is ideal for serverless environments and test scenarios where many connections are created and destroyed quickly.

### Key Settings

```python
# Connection string
DATABASE_URL = "postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require&prepared_statement_cache_size=0"

# Engine configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # Limit pool size 
    max_overflow=0,            # Prevent connection overflow
    pool_timeout=30,           # Connection timeout in seconds
    pool_recycle=1800,         # Recycle connections after 30 minutes
    pool_pre_ping=True         # Verify connections before use
)
```

### Important Notes for SQLAlchemy Connections

1. **SSL Mode**: Always use `ssl=true` for Supabase connections with asyncpg. (Note: psycopg2 uses `sslmode=require` instead)
2. **Prepared Statements**: Disable prepared statements with `prepared_statement_cache_size=0` when using Transaction Mode.
3. **Pool Settings**: Adjust pool size based on your application's needs:
   - For testing: 10-20 connections is usually sufficient
   - For production: Scale according to load
4. **Connection Recycling**: Set `pool_recycle` to avoid stale connections.
5. **Connection Pre-Ping**: Enable `pool_pre_ping` to verify connections before use.

## REST API Connection (Recommended)

Using the Supabase REST API provides a more reliable and consistent way to interact with the database, especially when direct database connections are problematic.

### Setting Up REST API Connection

```python
SUPABASE_URL = "https://[PROJECT_REF].supabase.co"
SUPABASE_KEY = "[SERVICE_ROLE_KEY]"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Example: List all projects
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/projects?select=*",
    headers=headers
)
```

### Advantages of REST API

1. **Reliability**: Works consistently across environments
2. **Simplicity**: No complex connection string or SSL issues
3. **Security**: Uses service role key with proper authentication
4. **Performance**: Efficiently handles queries through Supabase's optimized API
5. **Flexibility**: Easily switch between different Supabase projects

### Disadvantages of REST API

1. **Limited SQL Features**: Complex queries may be harder to express
2. **Additional Abstractions**: Not using SQLAlchemy directly
3. **Different Error Handling**: HTTP status codes instead of database exceptions

## Supabase Service Role Key

For integration tests and scripts that need full database access, use the Supabase service role key rather than the anon key. This can be found in:

1. Supabase Dashboard → Project Settings → API
2. Look for "service_role" key (never expose this in public-facing applications)

## Troubleshooting

1. **Connection Issues**: If you encounter connection problems, verify:
   - Your IP is allowed in Supabase's IP allow list
   - The service key is correct and not expired
   - The database URL format matches the connection type (check port and parameters)

2. **Pooler Connection Issues**: If pooler connections fail:
   - Try direct connection to verify credentials
   - Check Supabase status page for service issues
   - Verify SSL configuration

3. **Performance Issues**: If queries are slow:
   - Review connection pooling settings
   - Consider using session mode instead for long-running operations
   - Check query performance with Supabase's query tools

## Finding Connection Details

You can find your connection details in:
- Supabase Dashboard → Project Settings → Database
- Connection strings section (switch between direct or pooled connections)