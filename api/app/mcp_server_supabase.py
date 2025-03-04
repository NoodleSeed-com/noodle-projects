"""
Entry point for synchronous Supabase MCP server.
Uses the official supabase-py client and synchronous operations.
This is the main entry point for the MCP server.
"""
from app.mcp.synchronous import run

# Return the MCP server definition
server = run()