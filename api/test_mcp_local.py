#!/usr/bin/env python
"""
Test the MCP server locally by running 'mcp inspect' command.
"""
import subprocess
import sys
import os
import time

def test_mcp_server():
    """Test the MCP server by running the MCP inspect command."""
    print("Testing MCP server...")
    
    try:
        # Run mcp command to validate the server
        print("Starting MCP server...")
        server_process = subprocess.Popen(
            ["mcp", "run", "app/mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Run mcp inspect in a separate process
        print("Inspecting MCP server...")
        inspect_result = subprocess.run(
            ["mcp", "inspect", "http://localhost:8555"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Kill the server process
        server_process.terminate()
        server_process.wait(timeout=5)
        
        # Display results
        print("\nServer Output:")
        print(server_process.stdout.read())
        print("\nServer Errors:")
        print(server_process.stderr.read())
        
        print("\nInspect Output:")
        print(inspect_result.stdout)
        print("\nInspect Errors:")
        print(inspect_result.stderr)
        
        # Check if inspection was successful
        if "NoodleProjects" in inspect_result.stdout and inspect_result.returncode == 0:
            print("\n✅ MCP server is configured correctly!")
            return True
        else:
            print("\n❌ MCP server validation failed.")
            return False
    except Exception as e:
        print(f"\n❌ Error testing MCP server: {e}")
        return False
    finally:
        # Make sure to clean up any lingering processes
        try:
            server_process.terminate()
        except:
            pass

if __name__ == "__main__":
    test_mcp_server()