# -*- coding: utf-8 -*-
"""单 Agent：本地 tools + 业务库 tools + MCP tools（MCP 可降级）。"""
from __future__ import annotations

import os
from typing import Any, NotRequired

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ToolRetryMiddleware,
)
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.base import BaseStore

from app.hitl import apply_cli_hitl
from app.prompts import SUMMARY_PROMPT, SYSTEM_PROMPT
from mcp_server.loader import load_mcp_tools
from tools.biz_query import lookup_account, lookup_order, lookup_ticket
from tools.profile import get_user_info, save_user_info
from tools.weather import get_weather


class AgentStateWithUser(AgentState):
    """在默认 AgentState 上增加 user_id，供 Store 画像工具使用。"""

    user_id: NotRequired[str]

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"), override=True)

_DEFAULT_SUM_TRIGGER = 12
_DEFAULT_SUM_KEEP = 6
_DEFAULT_MAX_RETRIES = 2


def get_chat_model(**overrides: Any):
    """App 内共用对话模型（Agent / 路由等）。可用 overrides 覆盖 temperature 等。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")
    model_name = os.getenv("MODEL", "deepseek-flash")
    if not api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY（仓库根 .env）")

    params: dict[str, Any] = {
        "model": model_name,
        "model_provider": "openai",
        "api_key": api_key,
        "base_url": base_url,
    }
    params.update(overrides)
    return init_chat_model(**params)


def _sum_thresholds() -> tuple[int, int]:
    """SUM_TRIGGER_MESSAGES / SUM_KEEP_MESSAGES；非法或 keep>=trigger 时回退默认。"""
    try:
        trigger = int(os.getenv("SUM_TRIGGER_MESSAGES", str(_DEFAULT_SUM_TRIGGER)))
        keep = int(os.getenv("SUM_KEEP_MESSAGES", str(_DEFAULT_SUM_KEEP)))
    except ValueError:
        return _DEFAULT_SUM_TRIGGER, _DEFAULT_SUM_KEEP
    if trigger < 2 or keep < 1 or keep >= trigger:
        return _DEFAULT_SUM_TRIGGER, _DEFAULT_SUM_KEEP
    return trigger, keep


def _max_retries() -> int:
    """RETRY_MAX_RETRIES：模型/工具瞬时失败重试次数；0=关闭；非法回退默认。"""
    try:
        n = int(os.getenv("RETRY_MAX_RETRIES", str(_DEFAULT_MAX_RETRIES)))
    except ValueError:
        return _DEFAULT_MAX_RETRIES
    if n < 0:
        return _DEFAULT_MAX_RETRIES
    return n


def build_agent(*, enable_mcp: bool = True, store: BaseStore | None = None):
    model = get_chat_model()
    trigger, keep = _sum_thresholds()
    retries = _max_retries()

    tools: list = [
        get_weather,
        lookup_order,
        lookup_ticket,
        lookup_account,
    ]
    if store is not None:
        tools.extend([save_user_info, get_user_info])
    if enable_mcp:
        tools = tools + apply_cli_hitl(load_mcp_tools())

    print("当前 Agent tools:", [getattr(t, "name", str(t)) for t in tools])
    print(f"对话摘要: trigger={trigger} messages, keep={keep} messages")
    print(f"轻量重试: max_retries={retries}（0=关闭）")
    print(f"长期记忆 Store: {'已挂载' if store is not None else '未启用'}")

    middleware: list = [
        SummarizationMiddleware(
            model=get_chat_model(temperature=0),
            trigger=("messages", trigger),
            keep=("messages", keep),
            summary_prompt=SUMMARY_PROMPT,
        )
    ]
    # 工程兜底：瞬时失败有限次退避重试（非限流网关）
    if retries > 0:
        middleware.extend(
            [
                ModelRetryMiddleware(
                    max_retries=retries,
                    initial_delay=0.5,
                    backoff_factor=2.0,
                    max_delay=8.0,
                ),
                ToolRetryMiddleware(
                    max_retries=retries,
                    initial_delay=0.5,
                    backoff_factor=2.0,
                    max_delay=8.0,
                ),
            ]
        )

    # 短期：InMemorySaver；长期：可选 store；摘要/重试：middleware；发信 HITL：hitl.py
    kwargs: dict[str, Any] = {
        "model": model,
        "tools": tools,
        "system_prompt": SYSTEM_PROMPT,
        "checkpointer": InMemorySaver(),
        "middleware": middleware,
    }
    if store is not None:
        kwargs["store"] = store
        kwargs["state_schema"] = AgentStateWithUser
    return create_agent(**kwargs)
