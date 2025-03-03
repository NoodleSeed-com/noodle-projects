"""
Unified MCP server implementation with support for multiple connection methods.

This package provides a consolidated MCP server implementation that supports:
1. Direct SQLAlchemy database connection
2. Supabase REST API connection

It replaces the previous multiple implementations:
- mcp_server.py - Direct database connection
- mcp_server_rest.py - REST API connection  
- simple_mcp_server.py - Minimal implementation
- officialMCP.py - Official SDK implementation

Usage:
    # For direct database access (default):
    PYTHONPATH=. mcp dev app/mcp/server.py

    # For Supabase REST API:
    NOODLE_DB_CONNECTION_TYPE=supabase_rest PYTHONPATH=. mcp dev app/mcp/server.py
"""