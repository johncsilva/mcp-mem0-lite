#!/usr/bin/env python3
"""
Teste de integração real via MCP stdio.

- Sobe o servidor `server.py` em modo stdio (FastMCP)
- Chama `add_memory` e valida se a memória aparece em `list_memories`
- Faz cleanup com `delete_memory` para não sujar o banco

Uso:
    ./venv/bin/python test_mcp_stdio_integration.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE_DIR = Path(__file__).resolve().parent


def _extract_payload(result) -> dict[str, Any]:
    """Normaliza o resultado de call_tool em um dict plano."""
    if getattr(result, "structuredContent", None):
        return result.structuredContent or {}

    for item in getattr(result, "content", []) or []:
        if getattr(item, "type", None) == "text":
            try:
                return json.loads(item.text)
            except Exception:
                return {"raw_text": item.text}

    return {}


async def run(user_id: str | None = None):
    resolved_user = user_id or os.environ.get("DEFAULT_USER_ID") or "john"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(BASE_DIR / "server.py")],
        env={**os.environ, "DEFAULT_USER_ID": resolved_user},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            required = {"add_memory", "list_memories", "delete_memory"}
            missing = required - tool_names
            if missing:
                raise RuntimeError(f"Tools faltando no servidor MCP: {sorted(missing)}")

            text = f"[INTEGRATION] MCP stdio {int(time.time())}"
            add_resp = await session.call_tool(
                "add_memory",
                {"text": text, "user_id": resolved_user, "tags": ["integration", "mcp"]},
            )
            add_payload = _extract_payload(add_resp)
            memory_id = add_payload.get("id")
            results_block = add_payload.get("results")
            if not memory_id and isinstance(results_block, list) and results_block:
                memory_id = results_block[0].get("id")
            if not memory_id:
                raise RuntimeError(f"add_memory não retornou id. Payload: {add_payload}")

            list_resp = await session.call_tool(
                "list_memories", {"user_id": resolved_user, "limit": 50}
            )
            list_payload = _extract_payload(list_resp)
            memories = list_payload.get("memories") or list_payload.get("results") or []
            if isinstance(memories, dict):
                memories = (
                    memories.get("memories")
                    or memories.get("results")
                    or list(memories.values())
                )
            found = any(
                isinstance(m, dict) and text in (m.get("memory") or "")
                for m in (memories or [])
            )
            if not found:
                raise RuntimeError(
                    f"Memória recém-criada não apareceu em listagem. Payload: {list_payload}"
                )

            await session.call_tool(
                "delete_memory", {"memory_id": memory_id, "user_id": resolved_user}
            )

            print("✓ Integração MCP stdio OK:", memory_id)


if __name__ == "__main__":
    asyncio.run(run())
