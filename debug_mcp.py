"""Debug do registro de MCP tools"""

import sys
sys.path.insert(0, "C:\\Dev\\mcp-mem0-lite")

print("Importando FastMCP...")
from mcp.server.fastmcp import FastMCP

print("Criando instancia MCP...")
mcp = FastMCP("test-debug")

print(f"Lista de tools inicial: {mcp.list_tools()}")

print("\nRegistrando tool manualmente...")
@mcp.tool()
def test_tool(text: str) -> dict:
    """Test tool"""
    return {"result": text}

print(f"Lista de tools apos registro: {mcp.list_tools()}")

print("\nAgora testando import do server.py...")
import server

print(f"\nTools no server.mcp: {server.mcp.list_tools()}")
print(f"Total: {len(server.mcp.list_tools())}")
