#!/usr/bin/env python
"""Test if MCP imports work"""
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    print("✅ All MCP imports work!")
    print("✅ MCP package is correctly installed")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please activate your virtual environment and run: pip install -r requirements.txt")

# Made with Bob
