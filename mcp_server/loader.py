# -*- coding: utf-8 -*-
"""加载 MCP Server 工具；失败时返回空列表（降级）。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parent
_SERVER = _MCP_DIR / "server.py"


async def _load_tools_async():
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(
        {
            "news_server": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(_SERVER)],
                "cwd": str(_MCP_DIR),
            }
        }
    )
    return await client.get_tools()


def load_mcp_tools() -> list:
    if not _SERVER.exists():
        print(f"⚠️ MCP server 不存在: {_SERVER}")
        return []
    try:
        tools = asyncio.run(_load_tools_async())
        names = [getattr(t, "name", str(t)) for t in tools]
        print(f"✅ MCP 已连接，工具: {names}")
        return list(tools)
    except Exception as e:
        print(f"⚠️ MCP 未连接，将仅使用本地 tools。原因: {e}")
        return []
