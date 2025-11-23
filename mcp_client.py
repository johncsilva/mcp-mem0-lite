#!/usr/bin/env python3
"""
MCP Client Bridge - Connects Claude Desktop to existing MCP SSE server
"""
import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["C:\\Dev\\mcp-mem0-lite\\server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Keep connection open
            while True:
                await asyncio.sleep(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
