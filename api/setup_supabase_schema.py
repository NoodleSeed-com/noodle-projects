#!/usr/bin/env python
"""
Set up the Supabase schema using the seed.sql file.
This script requires admin access to the Supabase project.
"""
import os
import sys
import requests
from pathlib import Path

# Supabase configuration
SUPABASE_URL = "https://jsanjojgtyyfpnfqwhgx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDEwMjI0MjYsImV4cCI6MjA1NjU5ODQyNn0.Lp50rvIqDRgJUtb5iiSDG6o7Nw80gZRQ6bzfmCZ_-uM"

def get_seed_sql() -> str:
    """Read the seed SQL file."""
    seed_path = Path(__file__).parent.parent / "supabase" / "seed.sql"
    if not seed_path.exists():
        print(f"Error: Seed SQL file not found at {seed_path}")
        return ""
    
    with open(seed_path, "r") as f:
        sql_content = f.read()
    
    return sql_content

def main():
    """Set up the Supabase schema."""
    print(f"Setting up Supabase schema at {SUPABASE_URL}")
    
    # Read the seed SQL
    sql = get_seed_sql()
    if not sql:
        return False
    
    print("SQL script read from seed.sql file.")
    print("To set up the schema, you need to:")
    
    print("\n1. Log in to the Supabase dashboard at: https://app.supabase.com")
    print("2. Select your project: jsanjojgtyyfpnfqwhgx")
    print("3. Go to the 'Table Editor' tab")
    print("4. Click 'Query' at the top right to open the SQL editor")
    print("5. Paste and run the following SQL script:")
    print("\n" + "-" * 80 + "\n")
    print(sql)
    print("\n" + "-" * 80)
    
    print("\nNote: You need admin access to run this script.")
    print("The anon key provided doesn't have permission to execute SQL statements directly.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)