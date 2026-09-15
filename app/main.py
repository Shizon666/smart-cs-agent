# -*- coding: utf-8 -*-
"""
终端多轮入口（PyCharm 可直接 Run 本文件；Working directory = 仓库根目录）：
  python -m app.main
  python -m app.main --no-mcp
"""
from __future__ import annotations

import argparse
import asyncio
import os
import uuid
from typing import Any

from dotenv import load_dotenv

from app.agent import build_agent
from app.chat import run_repl
from app.routing import maybe_enrich

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"), override=True)


def _chunk_text(chunk: Any) -> str:
    """从 chat model stream chunk 取出可打印文本；工具规划轮常为空。"""
    if chunk is None:
        return ""
    content = getattr(chunk, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        bits: list[str] = []
        for part in content:
            if isinstance(part, str):
                bits.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                bits.append(str(part.get("text") or ""))
        return "".join(bits)
    return str(content) if content else ""


async def _astream_to_stdout(
    agent,
    content: str,
    *,
    thread_id: str,
    user_id: str | None = None,
) -> str:
    """
    流式约定（STREAM-01）：
    - 只打印 on_chat_model_stream 且 content 非空的片段（最终答复）
    - 工具调用轮不刷空 chunk；on_tool_start 打一行提示
    """
    config = {"configurable": {"thread_id": thread_id}}
    payload: dict[str, Any] = {
        "messages": [{"role": "user", "content": content}],
    }
    if user_id:
        payload["user_id"] = user_id
    parts: list[str] = []
    async for ev in agent.astream_events(
        payload,
        config=config,
        version="v2",
    ):
        kind = ev.get("event")
        if kind == "on_tool_start":
            name = ev.get("name") or "tool"
            print(f"\n（调用工具: {name}）\n", end="", flush=True)
            continue
        if kind != "on_chat_model_stream":
            continue
        piece = _chunk_text((ev.get("data") or {}).get("chunk"))
        if not piece:
            continue
        parts.append(piece)
        print(piece, end="", flush=True)
    return "".join(parts)


def _run_repl(*, enable_mcp: bool, store=None, user_id: str | None = None) -> None:
    agent = build_agent(enable_mcp=enable_mcp, store=store)
    session = {"thread_id": str(uuid.uuid4())}

    def _reply(text: str) -> str:
        content = maybe_enrich(text)
        return asyncio.run(
            _astream_to_stdout(
                agent,
                content,
                thread_id=session["thread_id"],
                user_id=user_id,
            )
        )

    def _clear() -> None:
        session["thread_id"] = str(uuid.uuid4())

    run_repl(_reply, on_clear=_clear)


def main():
    parser = argparse.ArgumentParser(description="smart-cs-agent 终端多轮对话")
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="不加载 MCP",
    )
    args = parser.parse_args()

    store_uri = (os.getenv("STORE_POSTGRES_URI") or "").strip()
    user_id = (os.getenv("STORE_USER_ID") or "demo-user").strip() or "demo-user"

    if not store_uri:
        print("长期记忆 Store: 未配置 STORE_POSTGRES_URI，仅短期记忆")
        _run_repl(enable_mcp=not args.no_mcp)
        return

    try:
        from langgraph.store.postgres import PostgresStore
    except ImportError as e:
        print(f"长期记忆 Store: 依赖缺失，降级为仅短期记忆。原因: {e}")
        _run_repl(enable_mcp=not args.no_mcp)
        return

    try:
        with PostgresStore.from_conn_string(store_uri) as store:
            store.setup()
            print(f"长期记忆 Store: Postgres 已连接；user_id={user_id}")
            _run_repl(enable_mcp=not args.no_mcp, store=store, user_id=user_id)
    except Exception as e:
        print(f"长期记忆 Store: 连接失败，降级为仅短期记忆。原因: {e}")
        _run_repl(enable_mcp=not args.no_mcp)


if __name__ == "__main__":
    main()
