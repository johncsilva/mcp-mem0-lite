import os
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import uvicorn

# Mem0 (pacote correto)
from mem0.memory.main import Memory

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8050"))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'mem0.db')}")

VECTOR_STORE_PROVIDER = os.getenv("VECTOR_STORE_PROVIDER", "chroma").lower()
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "768"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")

# Usuario padrao quando user_id nao for informado
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID") or os.getenv("USERNAME", "default")

# --- Helper Functions (precisam estar antes dos tools) -----------------------

def _merge_results_or(result_lists, limit: int = 5):
    """Une listas de resultados (OR lógico por tag), deduplica por id e retorna os top-N por score."""
    keep = {}
    for res in result_lists:
        for item in (res or []):
            mid = item.get("id")
            if not mid:
                continue
            cur = keep.get(mid)
            if not cur or float(item.get("score", 0)) > float(cur.get("score", 0)):
                keep[mid] = item
    # ordena por score desc e corta em limit
    merged = sorted(keep.values(), key=lambda x: float(x.get("score", 0)), reverse=True)
    return merged[:limit]


def _resolve_user_id(user_id: str | None) -> str:
    """Retorna o user_id fornecido ou o padrao configurado."""
    return user_id or DEFAULT_USER_ID


def _flatten_metadata(meta: dict | None) -> dict | None:
    if not meta:
        return None
    flat = {}
    for k, v in meta.items():
        if isinstance(v, list):
            flat[k] = ",".join(str(x) for x in v)  # lista -> string CSV
        elif isinstance(v, (str, int, float, bool)) or v is None:
            flat[k] = v
        else:
            flat[k] = str(v)  # qualquer outro tipo -> string
    return flat

# --- Mem0 Constructor --------------------------------------------------------

def build_mem0() -> Memory:
    """
    Monta o cliente Mem0 com SQLite + Chroma (vetor store local) + embeddings via Ollama.
    """
    if VECTOR_STORE_PROVIDER != "chroma":
        raise RuntimeError("Este servidor está configurado para usar apenas Chroma no momento.")

    # Build embedder config
    embedder_config = {
        "model": EMBEDDING_MODEL,
        "embedding_dims": EMBEDDING_DIMS,
    }
    if EMBEDDING_PROVIDER == "ollama":
        embedder_config["ollama_base_url"] = "http://127.0.0.1:11434"

    # Build LLM config
    llm_config = {
        "model": LLM_MODEL,
    }
    if LLM_PROVIDER == "ollama":
        llm_config["ollama_base_url"] = "http://127.0.0.1:11434"

    config = {
        "database": {
            "type": "sqlite",
            "connection_string": DATABASE_URL,
        },
        "vector_store": {
            "provider": "chroma",
            "config": {
                "path": CHROMA_PERSIST_DIR,
                "collection_name": "mem0_local"
            },
        },
        "embedder": {
            "provider": EMBEDDING_PROVIDER,
            "config": embedder_config
        },
        "llm": {
            "provider": LLM_PROVIDER,
            "config": llm_config
        },
    }
    return Memory.from_config(config)

mem0 = None

# --- MCP Server & Tools ------------------------------------------------------

mcp = FastMCP("mem0-lite")

@mcp.tool()
def add_memory(
    text: str,
    user_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None
) -> dict:
    """
    Adds a new memory to the vector store.

    Args:
        text: The content to store
        user_id: User identifier for memory isolation (defaults to DEFAULT_USER_ID env or USERNAME)
        tags: List of tags for categorization (stored as CSV in metadata)
        metadata: Additional metadata (lists are converted to CSV strings)

    Returns:
        Dictionary with memory details including id, hash, created_at
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)

    meta = _flatten_metadata(metadata) or {}
    if tags:
        meta["tags"] = ",".join(tags)

    result = mem0.add(text, user_id=user_id, metadata=meta if meta else None)
    clean = json.loads(json.dumps(result, default=str))

    # Normalize id for clients that expect a flat payload
    if isinstance(clean, dict) and "id" not in clean:
        nested = None
        if isinstance(clean.get("results"), list) and clean["results"]:
            nested = clean["results"][0]
        elif isinstance(clean.get("data"), list) and clean["data"]:
            nested = clean["data"][0]
        if isinstance(nested, dict) and nested.get("id"):
            clean["id"] = nested["id"]

    return clean


@mcp.tool()
def search_memory(
    query: str,
    user_id: str | None = None,
    tags: list[str] | None = None,
    filters: dict[str, str] | None = None,
    limit: int = 5,
    offset: int = 0
) -> dict:
    """
    Performs semantic search on stored memories.

    Args:
        query: Search query text
        user_id: User identifier for memory isolation (defaults to DEFAULT_USER_ID env or USERNAME)
        tags: List of tags for OR filtering (searches across all provided tags)
        filters: Additional metadata filters (e.g., {"priority": "should", "owner": "john"})
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)

    Returns:
        Dictionary with "results" key containing matched memories with scores
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)

    base_filters = filters.copy() if filters else {}

    # Single tag or no tags: direct search
    if not tags or len(tags) <= 1:
        if tags and len(tags) == 1:
            base_filters["tags"] = tags[0]
        results = mem0.search(query, user_id=user_id, filters=base_filters if base_filters else None, limit=limit + offset)
        # Apply offset and limit after search
        items = results.get("results", results) if isinstance(results, dict) else results
        paginated = items[offset:offset + limit] if isinstance(items, list) else items
        return {"results": json.loads(json.dumps(paginated, default=str)), "total": len(items) if isinstance(items, list) else 0, "offset": offset, "limit": limit}

    # Multiple tags: OR logic via multiple searches
    partials = []
    for tag in tags:
        filt = base_filters.copy()
        filt["tags"] = tag
        res = mem0.search(query, user_id=user_id, filters=filt, limit=limit + offset)
        items = res.get("results", res) if isinstance(res, dict) else res
        partials.append(items)

    merged = _merge_results_or(partials, limit=limit + offset)
    # Apply offset and limit after merge
    paginated = merged[offset:offset + limit]
    return {"results": json.loads(json.dumps(paginated, default=str)), "total": len(merged), "offset": offset, "limit": limit}


@mcp.tool()
def list_memories(user_id: str | None = None, limit: int = 100, offset: int = 0) -> dict:
    """
    Lists all memories for a specific user (defaults to DEFAULT_USER_ID env or USERNAME).

    Args:
        user_id: User identifier (defaults to DEFAULT_USER_ID env or USERNAME)
        limit: Maximum number of memories to return
        offset: Number of memories to skip (for pagination)

    Returns:
        Dictionary with "memories" key containing paginated memories for the user
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)

    memories = mem0.get_all(user_id=user_id)
    # Apply pagination
    total = len(memories) if isinstance(memories, list) else 0
    if isinstance(memories, list):
        paginated = memories[offset:offset + limit]
    else:
        paginated = memories

    return {
        "memories": json.loads(json.dumps(paginated, default=str)),
        "total": total,
        "offset": offset,
        "limit": limit
    }


@mcp.tool()
def list_all_user_ids() -> dict:
    """
    Lists all distinct user_ids that have stored memories.
    Useful to discover which users have data in the system.

    Returns:
        Dictionary with "user_ids" list and total count per user
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    try:
        # Acessa o vector store interno do Mem0 ao invés de criar nova instância
        vector_store = mem0.vector_store
        collection = vector_store.client.get_collection("mem0_local")
        results = collection.get(include=['metadatas'])

        # Count by user_id
        user_counts = {}
        for metadata in results['metadatas']:
            user_id = metadata.get('user_id', 'unknown')
            user_counts[user_id] = user_counts.get(user_id, 0) + 1

        return {
            "user_ids": list(user_counts.keys()),
            "counts": user_counts,
            "total_users": len(user_counts)
        }
    except Exception as e:
        return {"error": str(e), "user_ids": []}


@mcp.tool()
def delete_memory(memory_id: str, user_id: str | None = None) -> dict:
    """
    Deletes a specific memory by ID.

    Args:
        memory_id: The ID of the memory to delete
        user_id: User identifier (defaults to DEFAULT_USER_ID env or USERNAME)

    Returns:
        Dictionary with deletion status
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)

    result = mem0.delete(memory_id=memory_id)
    return {"status": "deleted", "memory_id": memory_id, "user_id": user_id, "result": json.loads(json.dumps(result, default=str))}


@mcp.tool()
def list_llm_options() -> dict:
    """
    Lists all available LLM configurations with their characteristics.

    Returns:
        Dictionary with available LLM providers and models
    """
    return {
        "current": {
            "provider": LLM_PROVIDER,
            "model": LLM_MODEL
        },
        "available": {
            "ollama": {
                "llama3.2:latest": {"speed": "~35s/memory", "cost": "free", "reliability": "good"},
                "llama3.1:8b": {"speed": "~60s/memory", "cost": "free", "reliability": "very good"},
                "tinyllama": {"speed": "~10s/memory", "cost": "free", "reliability": "may fail"}
            },
            "openai": {
                "gpt-4o-mini": {"speed": "~1-3s/memory", "cost": "~$0.00009/memory", "reliability": "excellent"},
                "gpt-4o": {"speed": "~1-3s/memory", "cost": "~$0.0003/memory", "reliability": "best"}
            }
        },
        "note": "Use change_llm_config() to switch providers"
    }


@mcp.tool()
def change_llm_config(provider: str, model: str) -> dict:
    """
    Changes the LLM provider and model dynamically without restarting the server.

    Args:
        provider: LLM provider ('ollama' or 'openai')
        model: Model name (e.g., 'llama3.2:latest', 'gpt-4o-mini')

    Returns:
        Dictionary with status and new configuration

    Examples:
        change_llm_config('openai', 'gpt-4o-mini')
        change_llm_config('ollama', 'llama3.2:latest')
    """
    global mem0, LLM_PROVIDER, LLM_MODEL

    # Validate provider
    if provider not in ['ollama', 'openai']:
        return {
            "status": "error",
            "message": f"Invalid provider '{provider}'. Must be 'ollama' or 'openai'",
            "valid_providers": ["ollama", "openai"]
        }

    # Store old config
    old_provider = LLM_PROVIDER
    old_model = LLM_MODEL

    try:
        # Update global variables
        LLM_PROVIDER = provider
        LLM_MODEL = model

        # Update .env file for persistence
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()

            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('LLM_PROVIDER='):
                        f.write(f'LLM_PROVIDER={provider}\n')
                    elif line.startswith('LLM_MODEL='):
                        f.write(f'LLM_MODEL={model}\n')
                    else:
                        f.write(line)

        # Rebuild Mem0 with new config
        mem0 = build_mem0()

        return {
            "status": "success",
            "message": f"LLM configuration changed successfully",
            "previous": {
                "provider": old_provider,
                "model": old_model
            },
            "current": {
                "provider": LLM_PROVIDER,
                "model": LLM_MODEL
            },
            "note": "Changes persist across server restarts"
        }

    except Exception as e:
        # Rollback on error
        LLM_PROVIDER = old_provider
        LLM_MODEL = old_model

        return {
            "status": "error",
            "message": f"Failed to change LLM config: {str(e)}",
            "current": {
                "provider": LLM_PROVIDER,
                "model": LLM_MODEL
            }
        }


# --- Lifecycle ---------------------------------------------------------------

@asynccontextmanager
async def lifespan(_):
    global mem0
    mem0 = build_mem0()
    yield

# --- app principal ------------------------------------------------------------

main_app = FastAPI()
main_app.router.lifespan_context = lifespan

# endpoints temporários de teste ----------------------------------------------

@main_app.get("/_test/add")
async def test_add(text: str, user_id: str = "default", tags: str | None = None):
    if mem0 is None:
        raise RuntimeError("Mem0 não foi inicializado")

    meta = None
    if tags and tags.strip():
        meta = {"tags": tags}  # mantém como CSV string

    item = mem0.add(
        text,
        user_id=user_id,
        metadata=meta
    )
    return json.loads(json.dumps(item, default=str))


@main_app.get("/_test/search")
async def test_search(
    query: str,
    user_id: str = "default",
    tags: str | None = None,      # pode ser "uma" ou "a,b,c"
    priority: str | None = None,
    owner: str | None = None,
    id: str | None = None,
    version: str | None = None,
    limit: int = 5
):
    """
    Busca semântica com filtros por tags e metacampos (igualdade).
    Se 'tags' tiver vírgula (ex.: DEV_RULE,delphi), aplica OR lógico no servidor.
    """
    if mem0 is None:
        raise RuntimeError("Mem0 não foi inicializado")
    # filtros escalares (sempre igualdade)
    base_filters = {}
    if priority:
        base_filters["priority"] = priority
    if owner:
        base_filters["owner"] = owner
    if id:
        base_filters["id"] = id
    if version:
        base_filters["version"] = version

    # caso 1: 0 ou 1 tag -> passa direto p/ mem0/chroma (igualdade simples)
    if not tags or not tags.strip() or "," not in tags:
        filt = base_filters.copy()
        if tags:
            filt["tags"] = tags  # uma única tag (str)
        results = mem0.search(query, user_id=user_id, filters=(filt or None), limit=limit)
        return {"results": json.loads(json.dumps(results, default=str))}

    # caso 2: várias tags -> faz N buscas (OR lógico) e une do lado do servidor
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    partials = []
    for t in tag_list:
        filt = base_filters.copy()
        filt["tags"] = t  # UMA tag por busca
        res = mem0.search(query, user_id=user_id, filters=filt, limit=limit)
        # 'res' costuma ser um dict com 'results' ou lista direta (dependendo da versão do mem0ai)
        items = res.get("results", res) if isinstance(res, dict) else res
        partials.append(items)

    merged = _merge_results_or(partials, limit=limit)
    return {"results": json.loads(json.dumps(merged, default=str))}


class AddPayload(BaseModel):
    text: str
    user_id: str = "default"
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@main_app.post("/_test/add_json")
async def test_add_json(payload: AddPayload):
    if mem0 is None:
        raise RuntimeError("Mem0 não foi inicializado")

    # Mescla tags no metadata
    meta = _flatten_metadata(payload.metadata) or {}
    if payload.tags:
        meta["tags"] = ",".join(payload.tags)  # tags como CSV no metadata

    item = mem0.add(
        payload.text,
        user_id=payload.user_id,
        metadata=meta if meta else None
    )
    return json.loads(json.dumps(item, default=str))



# endpoint de ajuda ------------------------------------------------------------

@main_app.get("/")
async def help_endpoint():
    """
    Documentation endpoint explaining how to use the MCP server.
    """
    return {
        "name": "MCP Mem0 Lite Server",
        "version": "1.0.0",
        "description": "Local memory store with semantic search using Mem0, Chroma, and Ollama",
        "status": "running",
        "endpoints": {
            "mcp": {
                "url": "/mcp/sse",
                "description": "MCP Server-Sent Events endpoint for Claude Desktop integration",
                "protocol": "SSE"
            },
            "test": {
                "add": "/_test/add?text=...&user_id=...&tags=...",
                "add_json": "/_test/add_json (POST)",
                "search": "/_test/search?query=...&user_id=...&tags=...&limit=..."
            }
        },
        "mcp_tools": {
            "add_memory": "Add new memory with text, tags, and metadata",
            "search_memory": "Semantic search with tags (OR logic) and filters",
            "list_memories": "List all memories for a user (paginated)",
            "list_all_user_ids": "Get all user_ids in the system",
            "delete_memory": "Delete a specific memory by ID",
            "list_llm_options": "Show available LLM configurations",
            "change_llm_config": "Switch LLM provider/model dynamically"
        },
        "configuration": {
            "current": {
                "llm_provider": LLM_PROVIDER,
                "llm_model": LLM_MODEL,
                "embedding_provider": EMBEDDING_PROVIDER,
                "embedding_model": EMBEDDING_MODEL,
                "vector_store": VECTOR_STORE_PROVIDER,
                "database": "sqlite" if "sqlite" in DATABASE_URL.lower() else "other"
            },
            "paths": {
                "database": DATABASE_URL,
                "chroma_persist": CHROMA_PERSIST_DIR
            }
        },
        "integration": {
            "claude_desktop": {
                "config_file": "~/.config/Claude/claude_desktop_config.json (Linux/WSL)",
                "example": {
                    "mcpServers": {
                        "mem0-lite": {
                            "command": "python",
                            "args": [str(Path(__file__).resolve())],
                            "env": {}
                        }
                    }
                }
            }
        },
        "usage": {
            "add_memory": {
                "example": "add_memory(text='Repository pattern for Delphi', tags=['delphi', 'architecture'], metadata={'priority': 'should'})"
            },
            "search_memory": {
                "example": "search_memory(query='delphi repository', tags=['delphi', 'architecture'], limit=10)",
                "notes": "Multiple tags use OR logic - returns memories matching ANY tag"
            },
            "list_memories": {
                "example": "list_memories(user_id='johnc', limit=50, offset=0)"
            }
        },
        "features": {
            "semantic_search": "Vector-based similarity search using embeddings",
            "local_storage": "SQLite + Chroma - all data stays on your machine",
            "tag_filtering": "OR logic across multiple tags",
            "metadata_filters": "Filter by custom fields (priority, owner, etc.)",
            "pagination": "Offset/limit support for large result sets",
            "dynamic_llm": "Switch LLM models without restarting"
        },
        "links": {
            "github": "https://github.com/yourusername/mcp-mem0-lite",
            "mem0_docs": "https://docs.mem0.ai/",
            "mcp_docs": "https://modelcontextprotocol.io/"
        }
    }

# montar o endpoint MCP SSE ----------------------------------------------------

sse_app = mcp.sse_app()
main_app.mount("/mcp", sse_app)  # sse_app tem /sse, então será acessível em /mcp/sse

app = main_app

# --- execução -----------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Detecta se está sendo chamado via stdio (Claude Desktop) ou SSE (servidor standalone)
    # Quando Claude Desktop chama, sys.stdin é um pipe, não um terminal
    if not sys.stdin.isatty():
        # Modo stdio para Claude Desktop - usa FastMCP diretamente
        mcp.run()
    else:
        # Modo SSE para outros clientes - inicia servidor HTTP
        uvicorn.run(app, host=HOST, port=PORT)
