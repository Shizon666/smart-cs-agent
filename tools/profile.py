# -*- coding: utf-8 -*-
"""用户画像长期记忆 Tool（LangGraph Store；对齐教程 chapter09）。"""
from __future__ import annotations

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime

_NAMESPACE = ("users",)


@tool
def save_user_info(name: str, runtime: ToolRuntime) -> str:
    """将用户姓名保存在长期记忆中（跨会话仍可读取）。

    Args:
        name: 用户自称的姓名或称呼
        runtime: 工具运行时（框架注入，勿向用户索要）
    """
    user_id = (runtime.state or {}).get("user_id")
    if not user_id:
        return "未提供 user_id，无法保存。"
    if runtime.store is None:
        return "长期记忆未启用，无法保存。"
    runtime.store.put(_NAMESPACE, user_id, {"name": name})
    return "saved"


@tool
def get_user_info(runtime: ToolRuntime) -> str:
    """从长期记忆中读取当前用户的姓名等信息。

    Args:
        runtime: 工具运行时（框架注入，勿向用户索要）
    """
    user_id = (runtime.state or {}).get("user_id")
    if not user_id:
        return "未提供 user_id，无法读取。"
    if runtime.store is None:
        return "长期记忆未启用，无法读取。"
    item = runtime.store.get(_NAMESPACE, user_id)
    return str(item.value) if item else "unknown"
