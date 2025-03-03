"""
Script to check database connection.
"""
import asyncio
import os
import pathlib
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = pathlib.Path("api/.env").resolve()
print(f"Loading .env file from: {env_path}")
print(f"File exists: {env_path.exists()}")
load_dotenv(env_path)

# Manually set the database URL if it's not loaded from .env
if "DATABASE_URL" not in os.environ:
    print("DATABASE_URL not found in environment variables, setting manually")
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:54342/postgres"

async def check_db():
    """Check database connection."""
    # Use the correct database URL directly
    db_url = "postgresql+asyncpg://postgres:postgres@127.0.0.1:54342/postgres"
    print(f"Using database URL: {db_url}")
    engine = create_async_engine(db_url)
    
    try:
        # Try to execute a simple query
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            
            # Check if projects table exists
            try:
                result = await conn.execute(text("SELECT * FROM projects LIMIT 1"))
                rows = result.fetchall()
                print(f"Projects table exists with {len(rows)} rows")
            except Exception as e:
                print(f"Error querying projects table: {e}")
            
            # Try to create a test table
            try:
                await conn.execute(text("CREATE TABLE IF NOT EXISTS test_table3 (id serial PRIMARY KEY, name text)"))
                await conn.execute(text("INSERT INTO test_table3 (name) VALUES ('test')"))
                await conn.commit()
                print("Test table created and data inserted")
                
                result = await conn.execute(text("SELECT * FROM test_table3"))
                rows = result.fetchall()
                print(f"Test table has {len(rows)} rows")
            except Exception as e:
                print(f"Error creating test table: {e}")
    except Exception as e:
        print(f"Database connection failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_db())
