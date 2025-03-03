#!/usr/bin/env python
"""
A simple MCP server using FastMCP following the official model.
This server is designed specifically for Claude Desktop integration.
"""
import sys
print("Simple MCP server starting...", file=sys.stderr)

from mcp.server.fastmcp import FastMCP

# Create the server instance
mcp = FastMCP("NoodleProjects")

# Add a simple health check tool for testing
@mcp.tool()
def check_health() -> dict:
    """Check if the server is healthy."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "server": "NoodleProjects"
    }

# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()