"""Kortex MCP Server"""

from fastmcp import FastMCP

mcp = FastMCP("Kortex")


if __name__ == "__main__":
    mcp.run()
