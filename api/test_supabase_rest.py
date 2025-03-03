#!/usr/bin/env python
"""
Test script to verify Supabase connection using the REST API instead of direct DB connection.
This is a workaround until we get the correct database credentials.
"""
import os
import json
import requests
import asyncio
import sys

# Supabase project details
SUPABASE_URL = "https://jsanjojgtyyfpnfqwhgx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzYW5qb2pndHl5ZnBuZnF3aGd4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTAyMjQyNiwiZXhwIjoyMDU2NTk4NDI2fQ.vVA1epNT0gGPCdoFfmmN0eIAhqKsVeujrc80qMyABJM"  # This is the service role key

def test_rest_api():
    """Test Supabase connection using the REST API."""
    print(f"\n\n🧪 Testing Supabase REST API connection")
    
    # Headers for authentication
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test a simple query to get database health
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/",
            headers=headers
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            print(f"✅ Successfully connected to Supabase REST API")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"❌ Connection error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def test_specific_table():
    """Test access to a specific table in Supabase."""
    print(f"\n\n🧪 Testing access to projects table")
    
    # Headers for authentication
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Query the projects table with a limit of 5 records
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/projects?select=*&limit=5",
            headers=headers
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            projects = response.json()
            if projects:
                print(f"✅ Successfully retrieved {len(projects)} projects from the database")
                print(f"First project: {json.dumps(projects[0], indent=2)}")
            else:
                print(f"✅ Connection successful but no projects found")
            return True
        else:
            print(f"❌ Query error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🔍 Testing Supabase REST API connection...")
    
    # First test the general API connection
    api_success = test_rest_api()
    
    if not api_success:
        print("\n❌ REST API connection failed. Skipping table tests.")
        return False
    
    # Then test access to the projects table
    table_success = test_specific_table()
    
    # Summary
    print("\n\n📊 Supabase REST API Test Summary:")
    print(f"REST API Connection: {'✅ Success' if api_success else '❌ Failed'}")
    print(f"Projects Table Access: {'✅ Success' if table_success else '❌ Failed'}")
    
    return api_success and table_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)