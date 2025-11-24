#!/usr/bin/env python3
"""
Debug script para investigar por que mem0.add() retorna {'results': []}
"""

import os
import json
from dotenv import load_dotenv
from mem0 import Memory

load_dotenv()

# Configuração do Mem0
config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "mem0",
            "path": os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
        }
    },
    "embedder": {
        "provider": os.getenv("EMBEDDING_PROVIDER", "ollama"),
        "config": {
            "model": os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            "embedding_dims": int(os.getenv("EMBEDDING_DIMS", "768")),
        }
    },
    "llm": {
        "provider": os.getenv("LLM_PROVIDER", "ollama"),
        "config": {
            "model": os.getenv("LLM_MODEL", "llama3.2:latest"),
            "temperature": 0.1,
            "max_tokens": 2000,
        }
    }
}

print("=" * 80)
print("Configuração do Mem0:")
print(json.dumps(config, indent=2))
print("=" * 80)

# Inicializa Mem0
mem0 = Memory.from_config(config)

# Teste 1: com infer=True (padrão)
print("\n[TESTE 1] Adicionando memória com infer=True")
text1 = "[INTEGRATION] MCP stdio test 123456"
result1 = mem0.add(text1, user_id="john", metadata={"tags": "integration,mcp"}, infer=True)
print(f"Resultado: {json.dumps(result1, indent=2, default=str)}")

# Teste 2: com infer=False
print("\n[TESTE 2] Adicionando memória com infer=False")
text2 = "[INTEGRATION] MCP stdio test 789012"
result2 = mem0.add(text2, user_id="john", metadata={"tags": "integration,mcp"}, infer=False)
print(f"Resultado: {json.dumps(result2, indent=2, default=str)}")

# Verifica memórias existentes
print("\n[VERIFICAÇÃO] Listando memórias do usuário john")
memories = mem0.get_all(user_id="john")
print(f"Total de memórias: {len(memories.get('results', []))}")
for i, mem in enumerate(memories.get("results", [])[:5]):
    print(f"  {i+1}. {mem.get('memory', '')[:80]}... (id={mem.get('id')})")
