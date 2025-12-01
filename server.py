import os
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel
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
# Mem0 usa history_db_path internamente; padronizamos para o arquivo local do projeto.
HISTORY_DB_PATH = os.getenv("HISTORY_DB_PATH", str(BASE_DIR / "mem0.db"))

VECTOR_STORE_PROVIDER = os.getenv("VECTOR_STORE_PROVIDER", "chroma").lower()
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))


def _get_chroma_collection_dimension(collection_name: str) -> int | None:
    """Reads collection dimension directly from Chroma's sqlite store (if present)."""
    db_path = Path(CHROMA_PERSIST_DIR) / "chroma.sqlite3"
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.execute("select dimension from collections where name=?", (collection_name,))
        row = cur.fetchone()
        return int(row[0]) if row else None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _resolve_chroma_collection_name() -> str:
    """
    Picks a collection name that matches the configured embedding dimensions.
    If the existing collection has a different dimension, suffix the name to avoid clashes.
    """
    base_name = os.getenv("CHROMA_COLLECTION_NAME", "mem0_local")
    existing_dim = _get_chroma_collection_dimension(base_name)
    if existing_dim is not None and existing_dim != EMBEDDING_DIMS:
        # Avoid reusing an incompatible collection; keep the old data under the old name.
        fallback = f"{base_name}_{EMBEDDING_DIMS}"
        print(
            f"[INFO] Collection '{base_name}' has dim {existing_dim}, expected {EMBEDDING_DIMS}; using '{fallback}'."
        )
        return f"{base_name}_{EMBEDDING_DIMS}"
    return base_name


EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "768"))

CHROMA_COLLECTION_NAME = _resolve_chroma_collection_name()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
# Controla se o mem0.add usa inferência de LLM (padrão: True)
MEM0_INFER = os.getenv("MEM0_INFER", "true").strip().lower() not in {"0", "false", "no"}

# Usuário padrão quando user_id não for informado (prioriza .env, depois USERNAME do SO)
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID") or os.getenv("USERNAME", "default")

# --- Cache de consultas ------------------------------------------------------
# Cache em memória para otimizar buscas frequentes
search_cache = {}
CACHE_TTL = timedelta(minutes=15)

# --- Schema de Regras de Programação -----------------------------------------
VALID_SEVERITIES = ["MUST", "SHOULD", "MAY", "DEPRECATED"]
VALID_CATEGORIES = ["security", "performance", "style", "architecture", "testing", "documentation", "general"]
VALID_CONTEXTS = ["dev", "production", "testing", "staging", "all"]
PLAN_STATUSES = {"active", "paused", "done"}
ITEM_STATUSES = {"todo", "doing", "done"}

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


def _expand_hierarchical_tags(tags: list[str]) -> list[str]:
    """
    Expande tags hierárquicas para incluir todos os níveis.
    Exemplo: ["python.django.security"] -> ["python.django.security", "python.django", "python", "security"]
    """
    if not tags:
        return []

    expanded = set()
    for tag in tags:
        # Adiciona a tag original
        expanded.add(tag)

        # Se tem pontos, adiciona todos os níveis
        if "." in tag:
            parts = tag.split(".")
            # Adiciona cada nível da hierarquia
            for i in range(1, len(parts) + 1):
                expanded.add(".".join(parts[:i]))
            # Adiciona também o último elemento (categoria final)
            expanded.add(parts[-1])

    return sorted(list(expanded))


def _validate_rule_schema(metadata: dict) -> tuple[bool, str]:
    """
    Valida schema de regras de programação.
    Retorna (is_valid, error_message)
    """
    if not metadata:
        return True, ""

    # Valida severity se presente
    if "severity" in metadata:
        if metadata["severity"] not in VALID_SEVERITIES:
            return False, f"Invalid severity '{metadata['severity']}'. Must be one of: {', '.join(VALID_SEVERITIES)}"

    # Valida category se presente
    if "category" in metadata:
        if metadata["category"] not in VALID_CATEGORIES:
            return False, f"Invalid category '{metadata['category']}'. Must be one of: {', '.join(VALID_CATEGORIES)}"

    # Valida context se presente
    if "context" in metadata:
        if metadata["context"] not in VALID_CONTEXTS:
            return False, f"Invalid context '{metadata['context']}'. Must be one of: {', '.join(VALID_CONTEXTS)}"

    return True, ""


def _get_from_cache(cache_key: str) -> dict | None:
    """Recupera resultado do cache se ainda válido"""
    if cache_key in search_cache:
        entry = search_cache[cache_key]
        if datetime.now() - entry['timestamp'] < CACHE_TTL:
            return entry['results']
        else:
            # Remove entrada expirada
            del search_cache[cache_key]
    return None


def _put_in_cache(cache_key: str, results: dict):
    """Armazena resultado no cache"""
    search_cache[cache_key] = {
        'results': results,
        'timestamp': datetime.now()
    }


def _clear_cache():
    """Limpa todo o cache (chamar após adicionar/deletar memórias)"""
    search_cache.clear()


def _make_cache_key(query: str, filters: dict, limit: int) -> str:
    """Gera chave única para cache baseado nos parâmetros de busca"""
    filter_str = json.dumps(filters, sort_keys=True) if filters else ""
    return f"{query}:{filter_str}:{limit}"


def _extract_id_from_mem0(clean: dict) -> str | None:
    """Extrai ID de resultados do mem0 (padrão add/search)."""
    if not isinstance(clean, dict):
        return None
    if clean.get("id"):
        return clean.get("id")
    nested = None
    if isinstance(clean.get("results"), list) and clean["results"]:
        nested = clean["results"][0]
    elif isinstance(clean.get("data"), list) and clean["data"]:
        nested = clean["data"][0]
    if isinstance(nested, dict):
        return nested.get("id")
    return None


def _parse_checklist(raw: Any) -> list[dict]:
    """Converte metadata.checklist (string JSON ou lista) em lista de itens."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _plan_memories_for_user(user_id: str) -> list[dict]:
    """Retorna apenas memórias do tipo plano para o user_id informado."""
    all_memories = mem0.get_all(user_id=user_id)
    memories_list = all_memories.get("results", all_memories) if isinstance(all_memories, dict) else all_memories
    return [m for m in (memories_list or []) if (m.get("metadata") or {}).get("rule_type") == "plan"]


def _find_plan_by_id(plan_id: str, user_id: str) -> dict | None:
    """Localiza o plano pelo plan_id no conjunto do usuário."""
    for plan in _plan_memories_for_user(user_id):
        meta = plan.get("metadata") or {}
        if meta.get("plan_id") == plan_id:
            return plan
    return None


def _normalize_plan_memory(memory_item: dict) -> dict:
    """Normaliza estrutura de plano para retorno dos tools."""
    metadata = (memory_item or {}).get("metadata") or {}
    checklist = _parse_checklist(metadata.get("checklist"))
    open_items = metadata.get("open_items")
    open_items = _coerce_int(open_items, sum(1 for item in checklist if item.get("status") != "done"))
    total_items = metadata.get("total_items")
    total_items = _coerce_int(total_items, len(checklist))

    return {
        "id": memory_item.get("id"),
        "plan_id": metadata.get("plan_id"),
        "title": memory_item.get("memory") or metadata.get("title"),
        "status": metadata.get("status", "active"),
        "priority": metadata.get("priority", "normal"),
        "due_date": metadata.get("due_date"),
        "open_items": open_items,
        "total_items": total_items,
        "checklist": checklist,
        "tags": metadata.get("tags"),
        "metadata": metadata,
    }


def _save_plan_memory(plan_memory: dict, metadata: dict, user_id: str) -> tuple[dict, str | None]:
    """Persiste mudanças de plano recriando a memória (mem0 não expõe update)."""
    title = plan_memory.get("memory") or metadata.get("title") or metadata.get("plan_id") or "Plano"
    add_result = mem0.add(title, user_id=user_id, metadata=metadata, infer=MEM0_INFER)
    clean = json.loads(json.dumps(add_result, default=str))

    # Se infer=True retornou results vazio, tenta novamente com infer=False
    if MEM0_INFER and isinstance(clean.get("results"), list) and not clean["results"]:
        add_result = mem0.add(title, user_id=user_id, metadata=metadata, infer=False)
        clean = json.loads(json.dumps(add_result, default=str))

    new_id = _extract_id_from_mem0(clean)
    warning = None

    # Remove a memória antiga para evitar duplicação do plan_id
    if plan_memory.get("id"):
        try:
            mem0.delete(memory_id=plan_memory["id"])
        except Exception as e:
            warning = f"Plano atualizado, mas falhou ao remover versão anterior: {e}"

    _clear_cache()

    normalized = _normalize_plan_memory({"id": new_id, "memory": title, "metadata": metadata})
    return normalized, warning


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
        "history_db_path": HISTORY_DB_PATH,
        "database": {
            "type": "sqlite",
            "connection_string": DATABASE_URL,
        },
        "vector_store": {
            "provider": "chroma",
            "config": {
                "path": CHROMA_PERSIST_DIR,
                "collection_name": CHROMA_COLLECTION_NAME
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

mem0 = build_mem0()

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

    # Normalize tags to list if a string was provided by the client
    normalized_tags: list[str] | None = None
    if isinstance(tags, str):
        normalized_tags = [tags]
    elif isinstance(tags, list):
        normalized_tags = tags

    meta = _flatten_metadata(metadata) or {}
    if normalized_tags:
        meta["tags"] = ",".join(normalized_tags)

    result = mem0.add(
        text,
        user_id=user_id,
        metadata=meta if meta else None,
        infer=MEM0_INFER
    )
    clean = json.loads(json.dumps(result, default=str))

    # Se infer=True retornou results vazio, tenta novamente com infer=False
    # Isso acontece quando o LLM decide que não há informação relevante
    if MEM0_INFER and isinstance(clean.get("results"), list) and not clean["results"]:
        result = mem0.add(
            text,
            user_id=user_id,
            metadata=meta if meta else None,
            infer=False
        )
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

    # Limpa cache após adicionar nova memória
    _clear_cache()

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

    # Verifica cache (ignora offset para simplificar)
    if offset == 0:
        cache_filters = base_filters.copy()
        if tags:
            cache_filters["_tags"] = ",".join(sorted(tags))
        cache_key = _make_cache_key(f"{query}:{user_id}", cache_filters, limit)
        cached = _get_from_cache(cache_key)
        if cached:
            return cached

    # Single tag or no tags: direct search
    if not tags or len(tags) <= 1:
        if tags and len(tags) == 1:
            base_filters["tags"] = tags[0]
        results = mem0.search(query, user_id=user_id, filters=base_filters if base_filters else None, limit=limit + offset)
        # Apply offset and limit after search
        items = results.get("results", results) if isinstance(results, dict) else results
        paginated = items[offset:offset + limit] if isinstance(items, list) else items
        response = {"results": json.loads(json.dumps(paginated, default=str)), "total": len(items) if isinstance(items, list) else 0, "offset": offset, "limit": limit}

        # Armazena no cache se offset == 0
        if offset == 0:
            _put_in_cache(cache_key, response)

        return response

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
    response = {"results": json.loads(json.dumps(paginated, default=str)), "total": len(merged), "offset": offset, "limit": limit}

    # Armazena no cache se offset == 0
    if offset == 0:
        _put_in_cache(cache_key, response)

    return response


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
        collection = vector_store.client.get_collection(CHROMA_COLLECTION_NAME)
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

    # Limpa cache após deletar
    _clear_cache()

    return {"status": "deleted", "memory_id": memory_id, "user_id": user_id, "result": json.loads(json.dumps(result, default=str))}


@mcp.tool()
def add_plan(
    title: str,
    items: list[str] | None = None,
    tags: list[str] | None = None,
    priority: str = "normal",
    due_date: str | None = None,
    status: str = "active",
    user_id: str | None = None
) -> dict:
    """
    Cria um novo plano com checklist.
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)

    if status not in PLAN_STATUSES:
        return {"status": "error", "message": f"Invalid status '{status}'. Must be one of: {', '.join(sorted(PLAN_STATUSES))}"}

    plan_id = str(uuid4())
    now = datetime.now().isoformat()
    checklist = []
    for item_title in (items or []):
        checklist.append({
            "id": str(uuid4()),
            "title": item_title,
            "status": "todo",
            "note": None,
            "created_at": now,
            "updated_at": now
        })

    base_tags = list(tags) if tags else []
    if "planning" not in base_tags:
        base_tags.append("planning")
    expanded_tags = _expand_hierarchical_tags(base_tags)
    open_items = sum(1 for item in checklist if item.get("status") != "done")

    metadata = {
        "rule_type": "plan",
        "plan_id": plan_id,
        "title": title,
        "status": status,
        "priority": priority,
        "due_date": due_date,
        "open_items": open_items,
        "total_items": len(checklist),
        "checklist": json.dumps(checklist),
        "created_at": now,
        "updated_at": now,
    }
    if expanded_tags:
        metadata["tags"] = ",".join(expanded_tags)

    result = mem0.add(title, user_id=user_id, metadata=metadata, infer=MEM0_INFER)
    clean = json.loads(json.dumps(result, default=str))

    # Se infer=True retornou results vazio, tenta novamente com infer=False
    if MEM0_INFER and isinstance(clean.get("results"), list) and not clean["results"]:
        result = mem0.add(title, user_id=user_id, metadata=metadata, infer=False)
        clean = json.loads(json.dumps(result, default=str))

    new_id = _extract_id_from_mem0(clean)
    normalized = _normalize_plan_memory({"id": new_id, "memory": title, "metadata": metadata})

    _clear_cache()

    response = {"status": "added", "plan_id": plan_id, "plan": normalized}
    if expanded_tags:
        response["tags"] = expanded_tags
    return response


@mcp.tool()
def list_plans(
    user_id: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    only_open: bool = False,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """
    Lista planos do usuário com filtros opcionais.
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)
    plans = _plan_memories_for_user(user_id)

    filtered = []
    for plan in plans:
        meta = plan.get("metadata") or {}
        if status and meta.get("status") != status:
            continue
        if only_open:
            open_items = _coerce_int(meta.get("open_items"), None)
            if open_items is None:
                checklist = _parse_checklist(meta.get("checklist"))
                open_items = sum(1 for item in checklist if item.get("status") != "done")
            if open_items <= 0:
                continue
        if tag:
            tag_list = [t.strip() for t in (meta.get("tags") or "").split(",") if t.strip()]
            if tag not in tag_list:
                continue
        filtered.append(_normalize_plan_memory(plan))

    total = len(filtered)
    paginated = filtered[offset:offset + limit]

    return {
        "plans": json.loads(json.dumps(paginated, default=str)),
        "total": total,
        "offset": offset,
        "limit": limit
    }


@mcp.tool()
def get_plan(plan_id: str, user_id: str | None = None) -> dict:
    """
    Recupera um plano específico pelo plan_id.
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)
    plan = _find_plan_by_id(plan_id, user_id)
    if not plan:
        return {"status": "not_found", "plan_id": plan_id}

    return {"status": "ok", "plan": json.loads(json.dumps(_normalize_plan_memory(plan), default=str))}


@mcp.tool()
def update_plan_item(
    plan_id: str,
    item_id: str,
    status: str,
    note: str | None = None,
    user_id: str | None = None
) -> dict:
    """
    Atualiza status/nota de um item do plano.
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)
    if status not in ITEM_STATUSES:
        return {"status": "error", "message": f"Invalid item status '{status}'. Must be one of: {', '.join(sorted(ITEM_STATUSES))}"}

    plan = _find_plan_by_id(plan_id, user_id)
    if not plan:
        return {"status": "not_found", "plan_id": plan_id}

    metadata = (plan.get("metadata") or {}).copy()
    checklist = _parse_checklist(metadata.get("checklist"))
    found = False
    now = datetime.now().isoformat()
    for item in checklist:
        if item.get("id") == item_id:
            item["status"] = status
            if note is not None:
                item["note"] = note
            item["updated_at"] = now
            found = True
            break

    if not found:
        return {"status": "not_found", "plan_id": plan_id, "item_id": item_id}

    metadata["checklist"] = json.dumps(checklist)
    metadata["open_items"] = sum(1 for i in checklist if i.get("status") != "done")
    metadata["total_items"] = len(checklist)
    metadata["updated_at"] = now
    # Preserva campos chave
    metadata["rule_type"] = "plan"
    metadata["plan_id"] = plan_id
    if "title" not in metadata:
        metadata["title"] = plan.get("memory")

    normalized, warning = _save_plan_memory(plan, metadata, user_id)
    response = {"status": "updated", "plan": json.loads(json.dumps(normalized, default=str))}
    if warning:
        response["warning"] = warning
    return response


@mcp.tool()
def add_plan_item(
    plan_id: str,
    title: str,
    user_id: str | None = None
) -> dict:
    """
    Adiciona um item ao checklist do plano.
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)
    plan = _find_plan_by_id(plan_id, user_id)
    if not plan:
        return {"status": "not_found", "plan_id": plan_id}

    metadata = (plan.get("metadata") or {}).copy()
    checklist = _parse_checklist(metadata.get("checklist"))
    now = datetime.now().isoformat()
    checklist.append({
        "id": str(uuid4()),
        "title": title,
        "status": "todo",
        "note": None,
        "created_at": now,
        "updated_at": now
    })

    metadata["checklist"] = json.dumps(checklist)
    metadata["open_items"] = sum(1 for i in checklist if i.get("status") != "done")
    metadata["total_items"] = len(checklist)
    metadata["updated_at"] = now
    metadata["rule_type"] = "plan"
    metadata["plan_id"] = plan_id
    if "title" not in metadata:
        metadata["title"] = plan.get("memory")

    normalized, warning = _save_plan_memory(plan, metadata, user_id)
    response = {"status": "updated", "plan": json.loads(json.dumps(normalized, default=str))}
    if warning:
        response["warning"] = warning
    return response


@mcp.tool()
def delete_plan(plan_id: str, user_id: str | None = None) -> dict:
    """
    Remove um plano (toda a memória associada).
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)
    plan = _find_plan_by_id(plan_id, user_id)
    if not plan:
        return {"status": "not_found", "plan_id": plan_id}

    mem0.delete(memory_id=plan.get("id"))
    _clear_cache()
    return {"status": "deleted", "plan_id": plan_id, "memory_id": plan.get("id")}


@mcp.tool()
def add_programming_rule(
    rule_text: str,
    language: str,
    category: str,
    severity: str = "SHOULD",
    framework: str | None = None,
    version: str = "1.0",
    context: str = "all",
    author: str | None = None,
    examples: dict[str, str] | None = None,
    related_rules: list[str] | None = None,
    replaces: str | None = None,
    user_id: str | None = None,
    additional_metadata: dict[str, Any] | None = None,
    check_duplicates: bool = True
) -> dict:
    """
    Adds a programming rule with structured metadata optimized for code guidelines.

    Args:
        rule_text: The rule description (supports markdown format)
        language: Programming language (e.g., 'python', 'delphi', 'go', 'javascript')
        category: Rule category (security, performance, style, architecture, testing, documentation, general)
        severity: Rule importance (MUST, SHOULD, MAY, DEPRECATED) - defaults to SHOULD
        framework: Specific framework if applicable (e.g., 'django', 'react', 'fastapi')
        version: Rule version for tracking changes (defaults to '1.0')
        context: Where rule applies (dev, production, testing, staging, all) - defaults to all
        author: Rule author/creator
        examples: Dictionary with 'correct' and 'incorrect' code examples
        related_rules: List of related rule IDs
        replaces: ID of rule that this one replaces (for deprecation tracking)
        user_id: User identifier (defaults to DEFAULT_USER_ID)
        additional_metadata: Any extra metadata fields
        check_duplicates: Check for similar rules before adding (defaults to True)

    Returns:
        Dictionary with rule details including id, or duplicate status if similar rule exists

    Example:
        add_programming_rule(
            rule_text="Always use parameterized queries to prevent SQL injection",
            language="python",
            category="security",
            severity="MUST",
            framework="django",
            examples={"correct": "User.objects.filter(id=user_id)", "incorrect": "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')"}
        )
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)

    # Valida severity, category, context
    if severity not in VALID_SEVERITIES:
        return {"status": "error", "message": f"Invalid severity '{severity}'. Must be one of: {', '.join(VALID_SEVERITIES)}"}

    if category not in VALID_CATEGORIES:
        return {"status": "error", "message": f"Invalid category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"}

    if context not in VALID_CONTEXTS:
        return {"status": "error", "message": f"Invalid context '{context}'. Must be one of: {', '.join(VALID_CONTEXTS)}"}

    # Verifica duplicatas se solicitado
    if check_duplicates:
        # Busca apenas em regras de programação da mesma linguagem e categoria
        duplicate_filters = {
            "rule_type": "programming_rule",
            "language": language.lower(),
            "category": category
        }
        similar = mem0.search(
            rule_text,
            user_id=user_id,
            filters=duplicate_filters,
            limit=1
        )
        items = similar.get("results", similar) if isinstance(similar, dict) else similar
        if items and len(items) > 0 and float(items[0].get("score", 0)) > 0.95:
            return {
                "status": "duplicate",
                "message": "Similar rule already exists",
                "existing_rule": json.loads(json.dumps(items[0], default=str)),
                "similarity_score": items[0].get("score")
            }

    # Constrói metadata estruturado
    metadata = {
        "language": language.lower(),
        "category": category,
        "severity": severity,
        "version": version,
        "context": context,
        "rule_type": "programming_rule",
        "created_at": datetime.now().isoformat()
    }

    if framework:
        metadata["framework"] = framework.lower()
    if author:
        metadata["author"] = author
    if examples:
        metadata["has_examples"] = True
        if "correct" in examples:
            metadata["example_correct"] = examples["correct"]
        if "incorrect" in examples:
            metadata["example_incorrect"] = examples["incorrect"]
    if related_rules:
        metadata["related_rules"] = ",".join(related_rules)
    if replaces:
        metadata["replaces"] = replaces

    # Adiciona metadata adicional se fornecido
    if additional_metadata:
        metadata.update(_flatten_metadata(additional_metadata) or {})

    # Cria tags hierárquicas automáticas
    tags = [language.lower(), category]
    if framework:
        tags.append(f"{language.lower()}.{framework.lower()}")
        tags.append(f"{language.lower()}.{framework.lower()}.{category}")
    else:
        tags.append(f"{language.lower()}.{category}")

    # Expande tags hierárquicas
    expanded_tags = _expand_hierarchical_tags(tags)
    metadata["tags"] = ",".join(expanded_tags)

    # Adiciona a regra
    result = mem0.add(rule_text, user_id=user_id, metadata=metadata, infer=MEM0_INFER)
    clean = json.loads(json.dumps(result, default=str))

    # Se infer=True retornou results vazio, tenta novamente com infer=False
    if MEM0_INFER and isinstance(clean.get("results"), list) and not clean["results"]:
        result = mem0.add(rule_text, user_id=user_id, metadata=metadata, infer=False)
        clean = json.loads(json.dumps(result, default=str))

    # Normaliza id
    if isinstance(clean, dict) and "id" not in clean:
        nested = None
        if isinstance(clean.get("results"), list) and clean["results"]:
            nested = clean["results"][0]
        elif isinstance(clean.get("data"), list) and clean["data"]:
            nested = clean["data"][0]
        if isinstance(nested, dict) and nested.get("id"):
            clean["id"] = nested["id"]

    # Limpa cache após adicionar
    _clear_cache()

    return {
        "status": "added",
        "rule": clean,
        "metadata": metadata,
        "tags": expanded_tags
    }


@mcp.tool()
def search_rules(
    query: str | None = None,
    language: str | None = None,
    category: str | None = None,
    severity: list[str] | None = None,
    framework: str | None = None,
    context: str | None = None,
    user_id: str | None = None,
    min_score: float = 0.6,
    limit: int = 10
) -> dict:
    """
    Searches programming rules with hybrid filtering (exact filters + semantic search).
    Optimized for code guidelines with caching support.

    Args:
        query: Semantic search query (optional - if None, returns all matching filters)
        language: Filter by programming language (exact match)
        category: Filter by category (exact match)
        severity: Filter by severity levels (list for OR logic, e.g., ["MUST", "SHOULD"])
        framework: Filter by framework (exact match)
        context: Filter by context where rule applies (exact match)
        user_id: User identifier (defaults to DEFAULT_USER_ID)
        min_score: Minimum similarity score (0.0-1.0) - defaults to 0.6
        limit: Maximum number of results to return

    Returns:
        Dictionary with filtered and scored results

    Examples:
        # Search for Python security rules
        search_rules(query="SQL injection", language="python", category="security")

        # Get all MUST rules for Django
        search_rules(language="python", framework="django", severity=["MUST"])

        # Semantic search across all Delphi rules
        search_rules(query="memory management", language="delphi", min_score=0.7)
    """
    if mem0 is None:
        raise RuntimeError("Mem0 not initialized")

    user_id = _resolve_user_id(user_id)

    # Constrói filtros exatos
    filters = {"rule_type": "programming_rule"}

    if language:
        filters["language"] = language.lower()
    if category:
        filters["category"] = category
    if framework:
        filters["framework"] = framework.lower()
    if context:
        filters["context"] = context

    # Verifica cache (apenas para queries com texto)
    if query:
        cache_key = _make_cache_key(f"{query}:{user_id}", filters, limit)
        cached = _get_from_cache(cache_key)
        if cached:
            return cached

    # Se tem múltiplos severities, faz OR logic
    if severity and len(severity) > 1:
        partials = []
        for sev in severity:
            filt = filters.copy()
            filt["severity"] = sev

            if query:
                res = mem0.search(query, user_id=user_id, filters=filt, limit=limit * 2)
            else:
                # Sem query, pega todas as memórias e filtra
                all_memories = mem0.get_all(user_id=user_id)
                # Trata caso get_all retorne dict ou list
                memories_list = all_memories.get("results", all_memories) if isinstance(all_memories, dict) else all_memories
                res = [m for m in memories_list if all(m.get("metadata", {}).get(k) == v for k, v in filt.items())]

            items = res.get("results", res) if isinstance(res, dict) else res
            partials.append(items)

        merged = _merge_results_or(partials, limit=limit * 2)
        results = merged
    else:
        # Severity único ou nenhum
        if severity and len(severity) == 1:
            filters["severity"] = severity[0]

        if query:
            res = mem0.search(query, user_id=user_id, filters=filters, limit=limit * 2)
            results = res.get("results", res) if isinstance(res, dict) else res
        else:
            # Sem query, pega todas as memórias e filtra
            all_memories = mem0.get_all(user_id=user_id)
            # Trata caso get_all retorne dict ou list
            memories_list = all_memories.get("results", all_memories) if isinstance(all_memories, dict) else all_memories
            results = [m for m in memories_list if all(m.get("metadata", {}).get(k) == v for k, v in filters.items())]

    # Filtra por min_score
    if query and results:
        filtered = [r for r in results if float(r.get("score", 0)) >= min_score]
    else:
        filtered = results

    # Limita resultados
    final_results = filtered[:limit] if filtered else []

    response = {
        "results": json.loads(json.dumps(final_results, default=str)),
        "total": len(final_results),
        "filters_applied": filters,
        "min_score": min_score,
        "query": query
    }

    # Armazena no cache se tinha query
    if query:
        _put_in_cache(cache_key, response)

    return response


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
    yield

# --- app principal ------------------------------------------------------------

main_app = FastAPI()
main_app.router.lifespan_context = lifespan

# endpoints temporários de teste ----------------------------------------------

@main_app.get("/_test/add")
async def test_add(text: str, user_id: str = DEFAULT_USER_ID, tags: str | None = None):
    if mem0 is None:
        raise RuntimeError("Mem0 não foi inicializado")

    resolved_user_id = _resolve_user_id(user_id)

    meta = None
    if tags and tags.strip():
        meta = {"tags": tags}  # mantém como CSV string

    item = mem0.add(
        text,
        user_id=resolved_user_id,
        metadata=meta,
        infer=MEM0_INFER
    )
    return json.loads(json.dumps(item, default=str))


@main_app.get("/_test/search")
async def test_search(
    query: str,
    user_id: str = DEFAULT_USER_ID,
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

    resolved_user_id = _resolve_user_id(user_id)
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
        results = mem0.search(query, user_id=resolved_user_id, filters=(filt or None), limit=limit)
        return {"results": json.loads(json.dumps(results, default=str))}

    # caso 2: várias tags -> faz N buscas (OR lógico) e une do lado do servidor
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    partials = []
    for t in tag_list:
        filt = base_filters.copy()
        filt["tags"] = t  # UMA tag por busca
        res = mem0.search(query, user_id=resolved_user_id, filters=filt, limit=limit)
        # 'res' costuma ser um dict com 'results' ou lista direta (dependendo da versão do mem0ai)
        items = res.get("results", res) if isinstance(res, dict) else res
        partials.append(items)

    merged = _merge_results_or(partials, limit=limit)
    return {"results": json.loads(json.dumps(merged, default=str))}


class AddPayload(BaseModel):
    text: str
    user_id: str = DEFAULT_USER_ID
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@main_app.post("/_test/add_json")
async def test_add_json(payload: AddPayload):
    if mem0 is None:
        raise RuntimeError("Mem0 não foi inicializado")

    resolved_user_id = _resolve_user_id(payload.user_id)
    # Mescla tags no metadata
    meta = _flatten_metadata(payload.metadata) or {}
    if payload.tags:
        meta["tags"] = ",".join(payload.tags)  # tags como CSV no metadata

    item = mem0.add(
        payload.text,
        user_id=resolved_user_id,
        metadata=meta if meta else None,
        infer=MEM0_INFER
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
            "add_plan": "Create a plan with checklist items",
            "list_plans": "List plans with optional filters (status, tag, only_open)",
            "get_plan": "Fetch a single plan by plan_id",
            "update_plan_item": "Mark/update a checklist item in a plan",
            "add_plan_item": "Append a new item to a plan",
            "delete_plan": "Remove a plan and its checklist",
            "add_programming_rule": "Add programming rule with structured metadata and validation",
            "search_rules": "Search rules with hybrid filtering (exact + semantic) and caching",
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
            },
            "add_plan": {
                "example": "add_plan(title='Entrega sprint', items=['Planejar tarefas', 'Implementar feature A'])"
            },
            "list_plans": {
                "example": "list_plans(status='active', only_open=True, limit=10)"
            },
            "update_plan_item": {
                "example": "update_plan_item(plan_id='abc', item_id='123', status='done')"
            },
            "add_programming_rule": {
                "example": "add_programming_rule(rule_text='Use parameterized queries', language='python', category='security', severity='MUST', framework='django')",
                "notes": "Automatically creates hierarchical tags and validates schema. Checks for duplicates by default."
            },
            "search_rules": {
                "example": "search_rules(query='SQL injection', language='python', category='security', min_score=0.7)",
                "notes": "Combines exact filters with semantic search. Results are cached for 15 minutes."
            }
        },
        "features": {
            "semantic_search": "Vector-based similarity search using embeddings",
            "local_storage": "SQLite + Chroma - all data stays on your machine",
            "tag_filtering": "OR logic across multiple tags",
            "metadata_filters": "Filter by custom fields (priority, owner, etc.)",
            "pagination": "Offset/limit support for large result sets",
            "dynamic_llm": "Switch LLM models without restarting",
            "hierarchical_tags": "Automatic tag expansion (python.django.security -> python, django, security)",
            "schema_validation": "Validates rule metadata (severity, category, context)",
            "deduplication": "Automatic detection of duplicate rules (configurable)",
            "query_caching": "15-minute cache for frequent searches (cleared on add/delete)",
            "hybrid_search": "Combines exact filtering with semantic similarity"
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
    # Permite forçar modo HTTP via variável de ambiente
    force_http = os.getenv("FORCE_HTTP_MODE", "false").lower() == "true"
    if not sys.stdin.isatty() and not force_http:
        # Modo stdio para Claude Desktop - usa FastMCP diretamente
        mcp.run()
    else:
        # Modo SSE para outros clientes - inicia servidor HTTP
        uvicorn.run(app, host=HOST, port=PORT)
