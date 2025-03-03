#!/usr/bin/env python
"""
Test script to verify Supabase connection options.
"""
import os
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

# Project reference from Supabase URL
PROJECT_REF = "jsanjojgtyyfpnfqwhgx"
REGION = "us-east-1"

# Async function to test database connection
async def test_connection(connection_url, mode_name):
    """Test the database connection with a given connection string."""
    print(f"\n\n🧪 Testing {mode_name} connection")
    print(f"Connection string: {connection_url}")
    
    try:
        # Create engine with minimal configuration for testing
        engine = create_async_engine(
            connection_url,
            echo=False,
            pool_pre_ping=True
        )
        
        # Test the connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT current_database(), current_user"))
            row = result.fetchone()
            if row:
                print(f"✅ Successfully connected to database: {row[0]} as user: {row[1]}")
                return True
            else:
                print("❌ Connection successful but no data returned")
                return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

async def main():
    """Try different connection modes to Supabase."""
    # Get password from environment or use default
    password = os.environ.get("DB_PASSWORD", "postgres")
    print(f"Using PROJECT_REF: {PROJECT_REF}")
    
    # Test all three connection types
    
    # 1. Direct connection
    direct_url = f"postgresql+asyncpg://postgres:{password}@db.{PROJECT_REF}.supabase.co:5432/postgres"
    direct_success = await test_connection(direct_url, "Direct")
    
    # 2. Session mode
    session_url = f"postgresql+asyncpg://postgres.{PROJECT_REF}:{password}@aws-0-{REGION}.pooler.supabase.com:5432/postgres"
    session_success = await test_connection(session_url, "Session Mode")
    
    # 3. Transaction mode
    transaction_url = f"postgresql+asyncpg://postgres.{PROJECT_REF}:{password}@aws-0-{REGION}.pooler.supabase.com:6543/postgres?prepared_statement_cache_size=0"
    transaction_success = await test_connection(transaction_url, "Transaction Mode")
    
    # Summary
    print("\n\n📊 Connection Test Summary:")
    print(f"Direct Connection: {'✅ Success' if direct_success else '❌ Failed'}")
    print(f"Session Mode: {'✅ Success' if session_success else '❌ Failed'}")
    print(f"Transaction Mode: {'✅ Success' if transaction_success else '❌ Failed'}")
    
    # Return success if any connection method worked
    return direct_success or session_success or transaction_success

if __name__ == "__main__":
    print("🔍 Testing Supabase connection options...")
    success = asyncio.run(main())
    sys.exit(0 if success else 1)