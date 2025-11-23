#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Benchmark add_memory speed with llama3.2:3b"""

import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, "C:\\Dev\\mcp-mem0-lite")

from server import add_memory, mem0, build_mem0
import server

# Initialize
if server.mem0 is None:
    print("Initializing Mem0 with llama3.2:latest...")
    server.mem0 = build_mem0()

print("\n" + "=" * 60)
print("BENCHMARK: add_memory com llama3.2:latest (3b)")
print("=" * 60)

test_text = "[BENCHMARK] Testing llama3.2 speed improvement - async patterns in Python"

print(f"\nAdding memory: '{test_text[:60]}...'")
print("Timing...")

start = time.time()
result = add_memory(
    text=test_text,
    user_id="benchmark",
    tags=["BENCHMARK", "speed_test"],
    metadata={"priority": "test"}
)
elapsed = time.time() - start

print(f"\n[RESULTADO]")
print(f"  Tempo total: {elapsed:.2f}s")
print(f"  Memory ID: {result.get('id', 'N/A')[:16]}...")

print("\n" + "=" * 60)
if elapsed < 30:
    print(f"SUCESSO! Reducao de ~{60/elapsed:.1f}x comparado ao llama3.1:8b")
    print(f"Velocidade esperada: 15-25s (obtido: {elapsed:.1f}s)")
else:
    print(f"ALERTA: Ainda lento ({elapsed:.1f}s). Considere:")
    print("  - Usar modelo ainda menor (phi3:mini, tinyllama)")
    print("  - Ativar GPU acceleration")
print("=" * 60)
