# MCP Mem0-Lite Setup Guide

## Configuração

### 1. Iniciar o Servidor

```bash
python server.py
```

O servidor estará disponível em:
- **REST API**: `http://127.0.0.1:8050`
- **MCP SSE**: `http://127.0.0.1:8050/sse`

### 2. Configurar Claude Desktop

Copie o conteúdo de `claude_desktop_config.json` para:

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS**:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux**:
```
~/.config/Claude/claude_desktop_config.json
```

### 3. Reiniciar Claude Desktop

Após copiar a configuração, reinicie o Claude Desktop para carregar o servidor MCP.

## MCP Tools Disponíveis

### `add_memory`
Adiciona uma nova memória ao vector store.

**Parâmetros**:
- `text` (string): Conteúdo a armazenar
- `user_id` (string, default="default"): ID do usuário
- `tags` (list[string], opcional): Tags para categorização
- `metadata` (dict, opcional): Metadados adicionais

**Exemplo**:
```json
{
  "text": "[DEV_RULE] Use async/await for I/O operations",
  "user_id": "john",
  "tags": ["DEV_RULE", "python", "async"],
  "metadata": {
    "priority": "must",
    "version": "2025-11-12"
  }
}
```

### `search_memory`
Busca semântica em memórias armazenadas.

**Parâmetros**:
- `query` (string): Texto de busca
- `user_id` (string, default="default"): ID do usuário
- `tags` (list[string], opcional): Filtro OR por tags
- `filters` (dict, opcional): Filtros adicionais de metadata
- `limit` (int, default=5): Máximo de resultados

**Exemplo**:
```json
{
  "query": "async patterns",
  "user_id": "john",
  "tags": ["DEV_RULE", "python"],
  "filters": {"priority": "must"},
  "limit": 3
}
```

### `list_memories`
Lista todas as memórias de um usuário.

**Parâmetros**:
- `user_id` (string, default="default"): ID do usuário
- `limit` (int, default=100): Máximo de memórias

### `delete_memory`
Remove uma memória específica.

**Parâmetros**:
- `memory_id` (string): ID da memória
- `user_id` (string, default="default"): ID do usuário (validação)

## Testando via REST API

### Adicionar memória:
```bash
curl -X POST http://127.0.0.1:8050/_test/add_json \
  -H "Content-Type: application/json" \
  -d @dev_rule_2.json
```

### Buscar memórias:
```bash
curl -X GET "http://127.0.0.1:8050/_test/search?query=FMX&user_id=john&limit=3"
```

## Arquitetura

```
┌─────────────────┐
│ Claude Desktop  │
│   MCP Client    │
└────────┬────────┘
         │ SSE (/sse)
         ▼
┌─────────────────┐
│   FastMCP       │
│   (server.py)   │
├─────────────────┤
│ MCP Tools:      │
│ - add_memory    │
│ - search_memory │
│ - list_memories │
│ - delete_memory │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Mem0        │
├─────────────────┤
│ - SQLite        │
│ - ChromaDB      │
│ - Ollama        │
└─────────────────┘
```

## Variáveis de Ambiente

Configuráveis via `.env`:

```env
HOST=127.0.0.1
PORT=8050
DATABASE_URL=sqlite:///C:/Dev/mcp-mem0-lite/mem0.db
VECTOR_STORE_PROVIDER=chroma
CHROMA_PERSIST_DIR=C:/Dev/mcp-mem0-lite/chroma_db
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMS=768
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
```

## Troubleshooting

### Erro "Mem0 not initialized"
- Verifique se o Ollama está rodando: `ollama list`
- Confirme que o modelo de embedding está disponível: `ollama pull nomic-embed-text`

### Claude Desktop não reconhece o servidor
- Verifique se o `server.py` está rodando
- Confirme que o caminho em `claude_desktop_config.json` está correto
- Reinicie o Claude Desktop após alterar a configuração

### Erro de conexão SSE
- Teste manualmente: `curl http://127.0.0.1:8050/sse`
- Verifique logs do servidor
