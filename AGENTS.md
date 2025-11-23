# Repository Guidelines for MCP Mem0-Lite

## Project Overview

**mcp-mem0-lite** is an MCP (Model Context Protocol) server that provides persistent memory capabilities using Mem0, ChromaDB (vector store), and Ollama (local LLM). It enables AI assistants to store and retrieve memories with semantic search.

### Architecture

- **Core Components**:
  - `server.py` - Main MCP server with dual-mode operation (stdio for Claude Desktop, SSE for other clients)
  - **Storage Stack**: SQLite (`mem0.db`) + ChromaDB (`chroma_db/`) + Ollama (LLM)
  - **Memory Processing Flow**: `add_memory()` → LLM processing (30-60s) → embedding → store

- **Key Architecture Decisions**:
  - Metadata flattening: Lists converted to CSV strings (ChromaDB limitation)
  - Multi-tag OR logic: Parallel searches merged server-side
  - User isolation: Defaults to Windows `USERNAME` env var
  - Dual-mode detection: `sys.stdin.isatty()` determines stdio vs HTTP mode

## Project Structure & Modules

```
mcp-mem0-lite/
├── server.py              # Main MCP server (625 lines) - Core logic
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

## Essential Commands

### Development & Testing
```bash
# Start server (hot path)
python server.py
# Server available at: http://127.0.0.1:8050 (REST) and /mcp/sse (SSE)

# Quick MCP tool validation
python test_mcp_tools.py
# Imports server, exercises add/search/list/delete; run with server running

# Check database state
python check_users.py
# Shows user_ids and memory counts

# Performance benchmarking
python benchmark_speed.py
# Tests add_memory speed with different LLM models

# Manual endpoint testing
curl -X POST http://127.0.0.1:8050/_test/add_json \
  -H "Content-Type: application/json" \
  -d '{"text":"test","user_id":"john","tags":["test"]}'

curl "http://127.0.0.1:8050/_test/search?query=test&user_id=john"

# Reset/clean database
./reset_memory.bat  # Windows
# Or manually:
rm mem0.db
rm -rf chroma_db/
```

### Windows Automation
```bash
# Automated startup (handles cleanup → Ollama check → server start → validation)
./start_mcp.bat

# Interactive startup with detailed output
./start_mcp_interactive.bat
```

### Integration Commands
```bash
# Claude Desktop integration
# Copy claude_desktop_config.json to OS-specific path and restart Claude

# Claude Code connection test
claude mcp list

# Claude Code test queries
claude mcp call mem0-lite add_memory '{"text":"test","user_id":"john"}'
```

## Environment Configuration

### .env file structure
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

**Critical**: Use forward slashes `/` even on Windows for cross-platform compatibility.

## MCP Tools Reference

All tools are defined in `server.py:116-407`:

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

## Coding Style & Naming Conventions

- **Language**: Python only; prefer 4-space indents
- **Function names**: Readable, imperative (`add_memory`, `build_mem0`, `_merge_results_or`)
- **Helper functions**: Keep module-local in `server.py` unless shared elsewhere
- **Environment keys**: Uppercase with underscores (`OPENAI_API_KEY`, `CHROMA_PERSIST_DIR`)
- **Script naming**: Favor small, single-purpose scripts; follow existing patterns (`check_*.py`, `start_mcp*.bat`)
- **Comments**: Use Portuguese for user-facing docs, English for code comments

## Implementation Patterns

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

### JSON Serialization
Always use `json.loads(json.dumps(result, default=str))` for datetime/complex types.

## Testing Guidelines

- **Primary test**: `python test_mcp_tools.py` as regression smoke test
- **When adding tools/endpoints**: Extend test script with clear printouts and exception handling
- **For REST/SSE changes**: Add curl examples to README_MCP_SETUP.md and exercise `/sse` manually
- **Performance testing**: Use `python benchmark_speed.py` for LLM model comparisons
- **Database validation**: Use `python check_users.py` to inspect state

## Performance Considerations

### Bottlenecks
- **Primary**: LLM processing in `add_memory` (30-60s on CPU)
- **Secondary**: Embedding generation (~1-2s)
- **Fast**: Search operations (~2-3s total)

### Optimization Options
1. **Smaller models**: `tinyllama` (~10s) vs `llama3.1:8b` (~60s)
2. **GPU acceleration**: 10-30x speedup if NVIDIA GPU available
3. **OpenAI API**: 1-3s response time (~$0.0001-0.001 per memory)
4. **Fast mode**: Skip LLM processing for instant storage (loses intelligence)

## Integration Guidelines

### Claude Desktop
- **Configuration**: Uses `claude_desktop_config.json` for stdio mode
- **Auto-detection**: Server detects Claude Desktop via `sys.stdin.isatty()`
- **Permissions**: Managed in `.claude/settings.local.json`

### Claude Code
- **Connection**: SSE endpoint at `http://127.0.0.1:8050/mcp/sse`
- **Permissions**: Auto-approved for all mem0-lite tools + curl + python
- **Testing**: `claude mcp list` and `claude mcp call` commands

### Other MCP Clients
- **Gemini CLI**: `gemini mcp add mem0-lite --command "npx" --args "-y" --args "mcp-remote@latest" --args "http://127.0.0.1:8050/mcp/sse"`
- **Codex**: `codex mcp add mem0-lite -- npx -y mcp-remote@latest http://127.0.0.1:8050/mcp/sse`

## Troubleshooting Common Issues

### "Mem0 not initialized"
- Verify Ollama is running: `curl http://127.0.0.1:11434/api/tags`
- Check embedding model exists: `ollama list | grep nomic-embed-text`

### Slow add_memory (60+ seconds)
- Using `llama3.1:8b` on CPU → switch to `llama3.2:latest` (~35s) or OpenAI
- See PERFORMANCE_TUNING.md for detailed options

### Port 8050 already in use
- Find process: `netstat -ano | grep 8050`
- Kill orphan servers before restart

### ChromaDB errors
- Delete and recreate: `rm -rf chroma_db/`
- Server will recreate on next start

### Memory ID errors (LLM returns invalid format)
- LLM too small (`tinyllama` sometimes fails)
- Use `llama3.2:latest` or larger

### Claude Desktop not connecting
- Verify server is running
- Check `claude_desktop_config.json` path and content
- Restart Claude Desktop after configuration changes

## Security & Configuration

### Never Commit
- `.env` files with secrets
- `mem0.db` or `chroma_db/` directories
- API keys or authentication tokens
- Any user data or memories

### Best Practices
- Keep `.env.example` updated when adding configuration
- Default to safe local values in examples
- Document minimal env changes when switching providers
- Rotate any leaked keys immediately
- Use relative paths in `.env.example`, absolute paths in production

### File Permissions
- Ensure `.env` has restricted permissions (600)
- Keep Claude configuration files in user directories only

## Commit & Pull Request Standards

### Commit Messages
- Use concise, imperative tense: `Add example env template`, `Harden add_memory validation`
- Include context for breaking changes
- Reference issues when relevant

### Pre-push Checklist
- Ensure `.env`/`mem0.db`/`chroma_db/` remain untracked
- Run `python test_mcp_tools.py` regression test
- Update `.env.example` if adding new configuration
- Test integration with at least one MCP client

### PR Requirements
- Brief description of the change and motivation
- Configuration impacts and migration steps if any
- Manual test steps (commands or curl examples)
- Screenshots only if UI clients are affected
- Performance implications if relevant

## Dependencies

Core packages (installation in INSTALACAO.md):
- `fastapi` - HTTP server framework
- `uvicorn` - ASGI server
- `mcp` (FastMCP) - MCP protocol implementation
- `mem0ai` - Memory management
- `chromadb` - Vector store
- `ollama` - LLM client
- `python-dotenv` - Environment management
- `pydantic` - Data validation

## Important Gotchas

1. **Dual-mode detection**: Server behavior changes based on `sys.stdin.isatty()` - test both modes
2. **Metadata flattening**: Lists become CSV strings - handle parsing on retrieval
3. **User defaults**: Uses Windows `USERNAME` if not specified - be explicit in tests
4. **LLM processing time**: `add_memory` can take 30-60s - implement appropriate timeouts
5. **Path handling**: Use forward slashes even on Windows
6. **JSON serialization**: Always use `json.loads(json.dumps(result, default=str))` for complex types
7. **Error handling**: Tools raise `RuntimeError` if Mem0 not initialized - handle gracefully in clients
