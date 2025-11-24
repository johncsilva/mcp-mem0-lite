"""
Debug helper to exercise Mem0 end-to-end and surface where it hangs.

Run from repo root:
    source .venv/bin/activate
    python debug_mem0.py
"""

import json
import os
import sqlite3
from pathlib import Path
import sys
import time

import requests
from dotenv import load_dotenv
from mem0.memory.main import Memory


def main():
    root = Path(__file__).resolve().parent
    print(f"CWD: {Path().resolve()}")
    env_path = root / ".env"
    if not env_path.exists():
        print(f"[WARN] .env not found at {env_path}")
    load_dotenv(env_path)

    # Build config honoring providers; avoid passing provider-specific keys.
    embed_dims = int(os.getenv("EMBEDDING_DIMS"))
    chroma_path = os.getenv("CHROMA_PERSIST_DIR")
    if not chroma_path:
        chroma_path = str(root / "chroma_db")

    def resolve_collection_name(base_name: str) -> str:
        db_path = Path(chroma_path) / "chroma.sqlite3"
        existing_dim = None
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.execute(
                    "select dimension from collections where name=?", (base_name,)
                )
                row = cur.fetchone()
                existing_dim = int(row[0]) if row else None
            except Exception:
                existing_dim = None
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        if existing_dim is not None and existing_dim != embed_dims:
            fallback = f"{base_name}_{embed_dims}"
            print(
                f"[WARN] Collection '{base_name}' has dim {existing_dim}, expected {embed_dims}; using '{fallback}'."
            )
            return fallback
        return base_name

    collection_name = resolve_collection_name(os.getenv("CHROMA_COLLECTION_NAME", "mem0_local"))

    embedder_config = {
        "model": os.getenv("EMBEDDING_MODEL"),
        "embedding_dims": embed_dims,
    }
    if os.getenv("EMBEDDING_PROVIDER") == "ollama":
        embedder_config["ollama_base_url"] = "http://127.0.0.1:11434"

    llm_config = {
        "model": os.getenv("LLM_MODEL"),
    }
    if os.getenv("LLM_PROVIDER") == "ollama":
        llm_config["ollama_base_url"] = "http://127.0.0.1:11434"

    config = {
        "database": {"type": "sqlite", "connection_string": os.getenv("DATABASE_URL")},
        "vector_store": {
            "provider": os.getenv("VECTOR_STORE_PROVIDER"),
            "config": {
                "path": chroma_path,
                "collection_name": collection_name,
            },
        },
        "embedder": {
            "provider": os.getenv("EMBEDDING_PROVIDER"),
            "config": embedder_config,
        },
        "llm": {
            "provider": os.getenv("LLM_PROVIDER"),
            "config": llm_config,
        },
    }
    print("Config:", json.dumps(config, indent=2))

    # Quick check to Ollama embeddings endpoint (only if provider is ollama)
    if config["embedder"]["provider"] == "ollama":
        payload = {"model": config["embedder"]["config"]["model"], "prompt": "ping"}
        print("\n[STEP] Testing Ollama embeddings endpoint...")
        try:
            t0 = time.time()
            r = requests.post(
                "http://127.0.0.1:11434/api/embeddings",
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            print(f"  OK in {time.time() - t0:.2f}s; keys: {list(r.json().keys())}")
        except Exception as e:
            print(f"  ERROR calling /api/embeddings: {e}")
            return
    else:
        print("\n[STEP] Skipping Ollama embeddings check (provider is not ollama).")

    print("\n[STEP] Building Mem0 client...")
    try:
        mem0 = Memory.from_config(config)
        print("  Mem0 ready.")
    except Exception as e:
        print(f"  ERROR building Mem0: {e}")
        return

    print("\n[STEP] mem0.add(infer=False)...")
    try:
        t0 = time.time()
        res = mem0.add(
            "ping",
            user_id=os.getenv("DEFAULT_USER_ID", "john"),
            metadata={"tags": "demo"},
            infer=False,  # bypasses LLM, forces embedding path
        )
        print(f"  Done in {time.time() - t0:.2f}s")
        print(json.dumps(res, indent=2, default=str))
    except Exception as e:
        print(f"  ERROR in mem0.add: {e}")
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
