#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path
import sqlite3
import chromadb
import sys

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "768"))


def _collection_dim(collection_name: str) -> int | None:
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


collection_name = os.getenv("CHROMA_COLLECTION_NAME", "mem0_local")
current_dim = _collection_dim(collection_name)
if current_dim is not None and current_dim != EMBEDDING_DIMS:
    alt = f"{collection_name}_{EMBEDDING_DIMS}"
    alt_dim = _collection_dim(alt)
    if alt_dim is not None:
        print(
            f"[WARN] Found '{collection_name}' with dim {current_dim}, expected {EMBEDDING_DIMS}. "
            f"Using '{alt}' (dim {alt_dim}) instead."
        )
        collection_name = alt
    else:
        print(
            f"[WARN] Collection '{collection_name}' has dim {current_dim}, expected {EMBEDDING_DIMS}. "
            "Proceeding anyway."
        )

# Connect to ChromaDB (respects CHROMA_PERSIST_DIR or defaults to local folder)
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Get collection
try:
    collection = client.get_collection(collection_name)

    dim = _collection_dim(collection_name)
    if dim:
        print(f"Collection '{collection_name}' dimension: {dim} (expected {EMBEDDING_DIMS})")

    # Get all data
    results = collection.get(include=['metadatas', 'documents'])

    print(f"Total memories: {len(results['ids'])}")

    # Group by user_id
    user_counts = {}
    for metadata in results['metadatas']:
        user_id = metadata.get('user_id', 'unknown')
        user_counts[user_id] = user_counts.get(user_id, 0) + 1

    print("\nMemorias por user_id:")
    for user_id, count in user_counts.items():
        print(f"  {user_id}: {count} memorias")

    print("\nPrimeiras 5 memorias:")
    for i in range(min(5, len(results['ids']))):
        print(f"\n  [{i+1}] ID: {results['ids'][i][:8]}...")
        print(f"      user_id: {results['metadatas'][i].get('user_id', 'N/A')}")
        print(f"      tags: {results['metadatas'][i].get('tags', 'N/A')}")
        print(f"      text: {results['documents'][i][:80]}...")

except Exception as e:
    print(f"Erro: {e}")
    print(f"Tipo: {type(e)}")
