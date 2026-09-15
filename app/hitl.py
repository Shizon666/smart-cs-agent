# -*- coding: utf-8 -*-
"""CLI 高危工具人工确认（HITL-01）。

仅拦截发信；天气/查单等不确认。拒绝则不调用原工具。
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

# 需人工确认的工具名（与 MCP server 一致）
_HITL_TOOL_NAMES = frozenset({"send_email_with_attachment"})


def apply_cli_hitl(tools: list) -> list:
    """对名单内工具包一层确认；其余原样返回。"""
    out: list = []
    for t in tools:
        name = getattr(t, "name", None)
        if name in _HITL_TOOL_NAMES:
            out.append(_wrap_with_confirm(t))
        else:
            out.append(t)
    return out


def _format_args(kwargs: dict[str, Any]) -> str:
    lines = []
    for key in ("to", "subject", "body", "filename"):
        if key in kwargs:
            val = kwargs[key]
            text = str(val)
            if key == "body" and len(text) > 200:
                text = text[:200] + "…"
            lines.append(f"  {key}: {text}")
    for key, val in kwargs.items():
        if key in ("to", "subject", "body", "filename"):
            continue
        lines.append(f"  {key}: {val}")
    return "\n".join(lines) if lines else f"  {kwargs!r}"


def _ask_confirm() -> bool:
    try:
        ans = input("确认发送邮件？[y/N]: ").strip().lower()
    except EOFError:
        return False
    return ans in {"y", "yes"}


def _wrap_with_confirm(tool: BaseTool) -> BaseTool:
    """包装后名称/参数 schema 不变，Agent 仍按原工具名调用。"""

    async def _arun(**kwargs: Any) -> str:
        print("\n—— 邮件发送需确认 ——", flush=True)
        print(_format_args(kwargs), flush=True)
        if not _ask_confirm():
            return "用户取消发送，未实际发信。"
        result = await tool.ainvoke(kwargs)
        return result if isinstance(result, str) else str(result)

    def _run(**kwargs: Any) -> str:
        print("\n—— 邮件发送需确认 ——", flush=True)
        print(_format_args(kwargs), flush=True)
        if not _ask_confirm():
            return "用户取消发送，未实际发信。"
        result = tool.invoke(kwargs)
        return result if isinstance(result, str) else str(result)

    return StructuredTool.from_function(
        func=_run,
        coroutine=_arun,
        name=tool.name,
        description=tool.description,
        args_schema=getattr(tool, "args_schema", None),
    )
