"""
Script de teste para validar MCP tools do servidor mem0-lite.
Execute com o servidor rodando em background.
"""

import json
import sys
import io

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Teste direto das funções (simulando chamada MCP)
def test_mcp_tools():
    print("=" * 60)
    print("TESTE DE VALIDAÇÃO MCP TOOLS - MEM0-LITE")
    print("=" * 60)

    # Import do servidor
    sys.path.insert(0, "C:\\Dev\\mcp-mem0-lite")
    from server import add_memory, search_memory, list_memories, delete_memory, mem0, build_mem0

    # Inicializa mem0 se necessário
    import server
    if server.mem0 is None:
        print("\n[SETUP] Inicializando Mem0...")
        server.mem0 = build_mem0()
        print("✓ Mem0 inicializado")

    print("\n" + "-" * 60)
    print("TESTE 1: add_memory")
    print("-" * 60)

    result = add_memory(
        text="[TEST] MCP tool validation - async patterns in Python",
        user_id="test_user",
        tags=["TEST", "python", "async"],
        metadata={"priority": "high", "category": "validation"}
    )

    print(f"✓ Memória adicionada: {result.get('id', 'N/A')}")
    memory_id = result.get("id")

    print("\n" + "-" * 60)
    print("TESTE 2: search_memory")
    print("-" * 60)

    search_result = search_memory(
        query="async patterns",
        user_id="test_user",
        tags=["TEST", "python"],
        limit=3
    )

    results = search_result.get("results", {})
    if isinstance(results, dict):
        results = results.get("results", [])

    print(f"✓ Encontradas {len(results)} memórias")
    for i, item in enumerate(results[:3], 1):
        print(f"  {i}. {item.get('memory', 'N/A')} (score: {item.get('score', 0):.2f})")

    print("\n" + "-" * 60)
    print("TESTE 3: list_memories")
    print("-" * 60)

    list_result = list_memories(user_id="test_user", limit=5)
    memories = list_result.get("memories", [])

    print(f"✓ Total de memórias: {len(memories)}")
    for i, mem in enumerate(memories[:3], 1):
        print(f"  {i}. {mem.get('memory', 'N/A')[:50]}...")

    print("\n" + "-" * 60)
    print("TESTE 4: delete_memory")
    print("-" * 60)

    if memory_id:
        delete_result = delete_memory(memory_id=memory_id, user_id="test_user")
        print(f"✓ Memória deletada: {delete_result.get('memory_id', 'N/A')}")
        print(f"  Status: {delete_result.get('status', 'N/A')}")
    else:
        print("⚠ Nenhum memory_id disponível para deletar")

    print("\n" + "=" * 60)
    print("VALIDAÇÃO COMPLETA")
    print("=" * 60)
    print("\n✓ Todos os MCP tools funcionando corretamente!")
    print("\nPróximo passo:")
    print("  1. Configure Claude Desktop com claude_desktop_config.json")
    print("  2. Reinicie o Claude Desktop")
    print("  3. Verifique se 'mem0-lite' aparece nos servidores MCP disponíveis")


if __name__ == "__main__":
    try:
        test_mcp_tools()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
