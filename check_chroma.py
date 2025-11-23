#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path
import chromadb
import sys

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))

# Connect to ChromaDB (respects CHROMA_PERSIST_DIR or defaults to local folder)
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Get collection
try:
    collection = client.get_collection("mem0_local")

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
