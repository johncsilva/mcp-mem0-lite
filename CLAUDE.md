# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mcp-mem0-lite** is an MCP (Model Context Protocol) server that provides persistent memory capabilities using Mem0, ChromaDB (vector store), and Ollama (local LLM). It enables AI assistants to store and retrieve memories with semantic search.

## Architecture

### Core Components

1. **server.py** - Main MCP server with dual-mode operation:
   - **stdio mode**: For Claude Desktop integration (direct MCP protocol)
   - **SSE mode**: For other clients like Claude Code, Gemini CLI (HTTP SSE endpoint at `/mcp/sse`)

   The server auto-detects mode: if `sys.stdin.isatty()` is False, uses stdio; otherwise starts HTTP server.

2. **Storage Stack**:
   - **SQLite** (`mem0.db`) - Stores memory metadata and relationships
   - **ChromaDB** (`chroma_db/`) - Vector embeddings for semantic search
   - **Ollama** - Local LLM inference (embeddings + memory processing)

3. **Memory Processing Flow**:
   ```
   add_memory() → LLM processing (30-60s) → embedding (1-2s) → store in SQLite + Chroma
   search_memory() → embedding (1-2s) → vector similarity search → results
   ```

### Key Architecture Decisions

- **Metadata flattening**: Lists in metadata are converted to CSV strings (server.py:50-61) because ChromaDB only supports scalar values
- **Multi-tag OR logic**: Multiple tags trigger parallel searches that are merged server-side (server.py:192-204) since ChromaDB doesn't support native OR operations
- **User isolation**: Defaults to Windows `USERNAME` env var if `user_id` not provided
- **Dynamic LLM switching**: `change_llm_config()` allows switching between Ollama/OpenAI without restart

## Development Commands

### Start Server

**For local development (SSE mode)**:
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Start server
python server.py
# Access at http://127.0.0.1:8050
# SSE endpoint at http://127.0.0.1:8050/mcp/sse
```

**For Claude Desktop (stdio mode)**:
```bash
# Claude Desktop automatically starts server in stdio mode
# Configured in claude_desktop_config.json
```

**Windows automated startup**:
```bash
.\start_mcp.bat
# Handles: cleanup → Ollama check → server start → validation
```

### Testing

**Test all MCP tools**:
```bash
python test_mcp_tools.py
```

**Check database state**:
```bash
python check_users.py
# Shows user_ids and memory counts
```

**Performance benchmarking**:
```bash
python benchmark_speed.py
# Tests add_memory speed with different LLM models
```

**Manual endpoint testing**:
```bash
# Add memory
curl -X POST http://127.0.0.1:8050/_test/add_json \
  -H "Content-Type: application/json" \
  -d '{"text":"test","user_id":"john","tags":["test"]}'

# Search
curl "http://127.0.0.1:8050/_test/search?query=test&user_id=john"
```

### Reset/Clean Database

```bash
.\reset_memory.bat  # Windows
# Or manually:
rm mem0.db
rm -rf chroma_db/
```

## Environment Configuration

**.env file structure**:
```env
# Server
HOST=127.0.0.1
PORT=8050

# Database
DATABASE_URL=sqlite:///mem0.db
VECTOR_STORE_PROVIDER=chroma
CHROMA_PERSIST_DIR=./chroma_db

# Embeddings (required)
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMS=768

# LLM for memory processing
LLM_PROVIDER=ollama  # or 'openai'
LLM_MODEL=llama3.2:latest

# Optional: OpenAI API
OPENAI_API_KEY=sk-...
```

**Critical paths**: Use forward slashes `/` even on Windows. On Windows, absolute paths like `C:/Dev/...` are used in production but relative paths work for development.

## MCP Tools Reference

All tools are defined in server.py:116-407:

1. **add_memory** (server.py:117-147)
   - Stores text with tags/metadata
   - Tags stored as CSV in metadata.tags
   - User defaults to Windows USERNAME
   - Returns: `{id, hash, created_at, ...}`

2. **search_memory** (server.py:150-204)
   - Semantic search with filters
   - Multiple tags use OR logic (parallel searches merged)
   - Pagination via offset/limit
   - Returns: `{results: [...], total, offset, limit}`

3. **list_memories** (server.py:207-240)
   - Lists all memories for user
   - Pagination support
   - Returns: `{memories: [...], total, offset, limit}`

4. **list_all_user_ids** (server.py:243-273)
   - Direct ChromaDB access (bypasses Mem0 API)
   - Returns: `{user_ids: [...], counts: {...}, total_users}`

5. **delete_memory** (server.py:276-296)
   - Deletes by memory_id
   - User validation

6. **list_llm_options** (server.py:299-324)
   - Shows available LLM configurations
   - Includes performance benchmarks

7. **change_llm_config** (server.py:327-406)
   - Runtime LLM switching
   - Updates .env file for persistence
   - Rebuilds Mem0 instance

## Common Development Patterns

### Adding New MCP Tools

```python
@mcp.tool()
def my_new_tool(param: str) -> dict:
    """
    Tool description for MCP clients.

    Args:
        param: Parameter description

    Returns:
        Result dictionary
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    # Implementation
    result = mem0.some_operation(param)
    return json.loads(json.dumps(result, default=str))
```

### Handling Metadata

Always flatten metadata before storing:
```python
meta = _flatten_metadata(user_metadata) or {}
if tags:
    meta["tags"] = ",".join(tags)
mem0.add(text, metadata=meta)
```

### Multi-tag OR Search Pattern

For multiple tags, run parallel searches and merge:
```python
partials = []
for tag in tags:
    filt = {"tags": tag}
    res = mem0.search(query, filters=filt, limit=limit)
    partials.append(res)
merged = _merge_results_or(partials, limit=limit)
```

## Performance Tuning

See PERFORMANCE_TUNING.md for details. Key points:

- **Bottleneck**: LLM processing in `add_memory` (30-60s on CPU)
- **Fast options**:
  - Use smaller models (tinyllama: ~10s)
  - Enable GPU acceleration (2-5s)
  - Use OpenAI API (1-3s, costs ~$0.0001/memory)
- **Embedding**: Fast (~1-2s), not the bottleneck
- **Search**: Fast (~2-3s total)

## Integration with Claude Code

**Configuration**: Claude Code uses `.claude/settings.local.json` for permissions and connects via SSE.

**Current permissions** (auto-approved):
- All mem0-lite tools (list_memories, add_memory, search_memory, list_all_user_ids, delete_memory)
- Bash commands: curl, python

**Connection**: Server runs on http://127.0.0.1:8050 with SSE endpoint at `/mcp/sse`

## Troubleshooting

**"Mem0 not initialized"**:
- Verify Ollama is running: `curl http://127.0.0.1:11434/api/tags`
- Check embedding model exists: `ollama list | grep nomic-embed-text`

**Slow add_memory (60+ seconds)**:
- Using llama3.1:8b on CPU → switch to llama3.2:latest (~35s) or OpenAI
- See PERFORMANCE_TUNING.md

**Port 8050 already in use**:
- Find process: `netstat -ano | grep 8050`
- Kill orphan servers before restart

**ChromaDB errors**:
- Delete and recreate: `rm -rf chroma_db/`
- Server will recreate on next start

**Memory ID errors** (LLM returns invalid format):
- LLM too small (tinyllama sometimes fails)
- Use llama3.2:latest or larger

## File Structure

```
mcp-mem0-lite/
├── server.py              # Main MCP server (625 lines)
├── .env                   # Configuration (use .env.example as template)
├── .env.example           # Template with default values
│
├── start_mcp.bat          # Windows: auto-start script
├── start_mcp_interactive.bat
├── reset_memory.bat       # Clear all data
│
├── test_mcp_tools.py      # Validation script
├── check_users.py         # DB inspection
├── benchmark_speed.py     # Performance testing
├── validate_mcp.py        # MCP protocol validation
│
├── INSTALACAO.md          # Complete installation guide (Portuguese)
├── README_MCP_SETUP.md    # Quick setup guide
├── PERFORMANCE_TUNING.md  # Optimization guide
│
├── claude_desktop_config.json  # Claude Desktop integration
├── .claude/
│   └── settings.local.json     # Claude Code permissions
│
├── mem0.db               # SQLite database (created at runtime)
└── chroma_db/            # Vector store (created at runtime)
```

## Important Implementation Notes

1. **Dual-mode detection** (server.py:619-624): Uses `sys.stdin.isatty()` to choose stdio vs HTTP mode
2. **Lifecycle management** (server.py:411-415): `lifespan` context manager initializes Mem0 on startup
3. **JSON serialization**: Always use `json.loads(json.dumps(result, default=str))` for datetime/complex types
4. **Path handling**: Use forward slashes even on Windows for cross-platform compatibility
5. **Error handling**: Tools raise `RuntimeError` if Mem0 not initialized; clients should handle gracefully

## Dependencies

Core packages (see installation commands in INSTALACAO.md):
- `fastapi` - HTTP server framework
- `uvicorn` - ASGI server
- `mcp` (FastMCP) - MCP protocol implementation
- `mem0ai` - Memory management
- `chromadb` - Vector store
- `ollama` - LLM client
- `python-dotenv` - Environment management
- `pydantic` - Data validation
