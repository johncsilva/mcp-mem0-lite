"""Validação rápida da estrutura MCP tools"""

import sys
sys.path.insert(0, "C:\\Dev\\mcp-mem0-lite")

from server import mcp

print("=" * 60)
print("VALIDACAO MCP TOOLS - MEM0-LITE")
print("=" * 60)

# Obter lista de tools registrados via _tool_manager
tools = {}
if hasattr(mcp, '_tool_manager'):
    tool_manager = mcp._tool_manager
    if hasattr(tool_manager, '_tools'):
        tools = tool_manager._tools
    elif hasattr(tool_manager, 'tools'):
        tools = tool_manager.tools

print(f"\nTotal de tools registrados: {len(tools)}")
print("\nTools disponíveis:")

expected_tools = ["add_memory", "search_memory", "list_memories", "delete_memory"]

for tool_name in expected_tools:
    status = "[OK]" if tool_name in tools else "[FALTANDO]"
    print(f"  {status} {tool_name}")

print("\n" + "=" * 60)

if len(tools) == 4:
    print("STATUS: Todos os MCP tools implementados corretamente!")
    print("\nProximos passos:")
    print("  1. Copie claude_desktop_config.json para a pasta do Claude Desktop")
    print("  2. Inicie o servidor: python server.py")
    print("  3. Reinicie o Claude Desktop")
    print("  4. Verifique se 'mem0-lite' aparece nos servidores MCP")
else:
    print(f"STATUS: Faltam {4 - len(tools)} tools!")
    sys.exit(1)
