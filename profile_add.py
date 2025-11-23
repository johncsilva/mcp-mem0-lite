#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Profile add_memory operation to identify bottlenecks"""

import time
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, "C:\\Dev\\mcp-mem0-lite")

from server import build_mem0

print("=" * 60)
print("PROFILING add_memory OPERATION")
print("=" * 60)

# Initialize mem0
print("\n[1] Initializing Mem0...")
t0 = time.time()
mem0 = build_mem0()
t1 = time.time()
print(f"    [OK] Initialization: {t1-t0:.2f}s")

# Add memory
test_text = "[PROFILE TEST] Testing memory addition performance with Llama3.1"
test_meta = {"tags": "PROFILE,test", "priority": "low"}

print(f"\n[2] Adding memory: '{test_text[:50]}...'")
t2 = time.time()
result = mem0.add(test_text, user_id="profile_test", metadata=test_meta)
t3 = time.time()
print(f"    [OK] Total add_memory time: {t3-t2:.2f}s")

print(f"\n[3] Result: {result}")

print("\n" + "=" * 60)
print(f"TOTAL TIME: {t3-t0:.2f}s")
print("=" * 60)

print("\nBottlenecks likely:")
print("  1. LLM processing (extracting/structuring memory)")
print("  2. Embedding generation (nomic-embed-text)")
print("  3. Deduplication checks (semantic search)")
print("\nTo speed up: disable LLM processing or use faster models")
