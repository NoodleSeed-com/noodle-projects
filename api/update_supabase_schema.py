#!/usr/bin/env python
"""
Utility to update the Supabase database schema using the project's schema definition.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://jsanjojgtyyfpnfqwhgx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDEwMjI0MjYsImV4cCI6MjA1NjU5ODQyNn0.Lp50rvIqDRgJUtb5iiSDG6o7Nw80gZRQ6bzfmCZ_-uM"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_sql_commands() -> list:
    """Read the SQL commands from the seed file."""
    seed_path = Path(__file__).parent.parent / "supabase" / "seed.sql"
    if not seed_path.exists():
        logger.error(f"Seed SQL file not found at {seed_path}")
        return []
    
    with open(seed_path, "r") as f:
        sql_content = f.read()
    
    # Split the SQL content into individual commands
    # This simple approach assumes each command ends with a semicolon
    commands = []
    current_command = []
    
    for line in sql_content.split('\n'):
        # Skip comments
        if line.strip().startswith('--'):
            continue
        
        current_command.append(line)
        
        if line.strip().endswith(';'):
            commands.append('\n'.join(current_command))
            current_command = []
    
    # Add any remaining command without a semicolon
    if current_command:
        commands.append('\n'.join(current_command))
    
    return commands

async def check_table_exists(supabase: Client, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        # Try to select from the table
        response = supabase.table(table_name).select('*').limit(1).execute()
        return True
    except Exception as e:
        if 'relation "' + table_name + '" does not exist' in str(e):
            return False
        logger.error(f"Error checking table {table_name}: {e}")
        return False

async def check_column_exists(supabase: Client, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        # Try to select the specific column
        response = supabase.table(table_name).select(column_name).limit(1).execute()
        return True
    except Exception as e:
        if f"Could not find the '{column_name}' column" in str(e):
            return False
        logger.error(f"Error checking column {column_name} in table {table_name}: {e}")
        return False

async def update_schema():
    """Update the Supabase database schema."""
    try:
        logger.info(f"Connecting to Supabase at {SUPABASE_URL}")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if 'projects' table exists and has 'active' column
        if await check_table_exists(supabase, 'projects'):
            logger.info("Projects table exists")
            if not await check_column_exists(supabase, 'projects', 'active'):
                logger.info("Adding 'active' column to projects table")
                # Using the REST API to execute SQL (this requires additional permissions)
                # This is a workaround since the Supabase Python client doesn't support raw SQL directly
                try:
                    # This would require appropriate permissions and might not work with anon key
                    await execute_sql(supabase, "ALTER TABLE projects ADD COLUMN active boolean NOT NULL DEFAULT true;")
                    logger.info("Successfully added 'active' column")
                except Exception as e:
                    logger.error(f"Failed to add 'active' column: {e}")
                    return False
            else:
                logger.info("'active' column already exists in projects table")
        else:
            logger.info("Projects table does not exist, need to create schema from scratch")
            # Creating from scratch would require executing all SQL commands
            # This might not be possible with the anon key
            logger.error("Full schema creation not supported with current permissions")
            return False
        
        logger.info("Schema update completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
        return False

async def execute_sql(supabase: Client, sql: str):
    """
    Execute raw SQL through the Supabase REST API.
    
    Note: This is a workaround and may not work with an anon key.
    Proper SQL execution would require:
    1. Using the Postgres connection directly (requires service role key)
    2. Using Supabase's SQL editor interface
    3. Using a database migration tool like Flyway or Liquibase
    """
    # This is a placeholder - current Python client doesn't support raw SQL execution
    # In practice, you'd need to use a service role key and possibly a different API endpoint
    raise NotImplementedError("Raw SQL execution not supported with current client credentials")

if __name__ == "__main__":
    success = asyncio.run(update_schema())
    exit(0 if success else 1)