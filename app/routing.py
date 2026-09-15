# -*- coding: utf-8 -*-
"""意图路由 + 按需拼装知识库上下文（E1）。"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.agent import get_chat_model
from app.prompts import ROUTE_SYSTEM_PROMPT
from rag.retrieve import format_hits_as_context, retrieve

_INTENTS = frozenset(
    {
        "knowledge",
        "order",
        "ticket",
        "account",
        "weather",
        "mcp_news",
        "chitchat",
        "unknown",
    }
)

_RE_ORDER = re.compile(r"\bORD\d+\b", re.I)
_RE_TICKET = re.compile(r"\bT\d+\b", re.I)
_RE_ACCOUNT = re.compile(r"\bU\d+\b", re.I)

_WEATHER_MARKERS = (
    "天气",
    "气温",
    "下雨",
    "下雪",
    "降水",
    "湿度",
    "风速",
    "预报",
    "几度",
)
_NEWS_MARKERS = ("新闻", "舆情", "情感分析", "发邮件", "搜索一下")


@dataclass
class RouteResult:
    intent: str
    need_rag: bool
    search_query: str = ""
    reason: str = ""


def try_rule_route(text: str) -> RouteResult | None:
    """硬规则短路径；命中则不再调用 LLM。"""
    raw = (text or "").strip()
    if not raw:
        return RouteResult("unknown", True, "", "空输入偏检索")

    if _RE_ORDER.search(raw) and any(
        k in raw for k in ("订单", "状态", "查", "进度", "退款")
    ):
        return RouteResult("order", False, "", "规则:订单号查询")
    if _RE_ORDER.search(raw):
        return RouteResult("order", False, "", "规则:含订单号")

    if _RE_TICKET.search(raw):
        return RouteResult("ticket", False, "", "规则:含工单号")

    if _RE_ACCOUNT.search(raw) and any(
        k in raw for k in ("额度", "账号", "用户", "剩余", "套餐")
    ):
        return RouteResult("account", False, "", "规则:账号额度")
    if _RE_ACCOUNT.search(raw):
        return RouteResult("account", False, "", "规则:含用户ID")

    if any(m in raw for m in _WEATHER_MARKERS):
        return RouteResult("weather", False, "", "规则:天气")

    if any(m in raw for m in _NEWS_MARKERS):
        return RouteResult("mcp_news", False, "", "规则:新闻/舆情/邮件")

    return None


def _parse_llm_json(content: str) -> RouteResult:
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    intent = str(data.get("intent") or "unknown").strip().lower()
    if intent not in _INTENTS:
        intent = "unknown"
    need_rag = data.get("need_rag")
    if need_rag is None:
        need_rag = True
    need_rag = bool(need_rag)
    if intent == "unknown":
        need_rag = True
    search_query = str(data.get("search_query") or "").strip()
    reason = str(data.get("reason") or "llm").strip()
    return RouteResult(intent, need_rag, search_query, reason)


def llm_route(text: str) -> RouteResult:
    model = get_chat_model(temperature=0)
    msg = model.invoke(
        [
            {"role": "system", "content": ROUTE_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]
    )
    content = getattr(msg, "content", str(msg))
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", part)) if isinstance(part, dict) else str(part)
            for part in content
        )
    return _parse_llm_json(str(content))


def route_message(text: str) -> RouteResult:
    """规则优先；否则 LLM；失败则 unknown + need_rag=true。"""
    hit = try_rule_route(text)
    if hit is not None:
        return hit
    try:
        return llm_route(text)
    except Exception as e:
        return RouteResult(
            "unknown",
            True,
            (text or "").strip()[:30],
            f"路由降级:{e}",
        )


_RAG_HINT = (
    "【知识库检索，仅供产品/政策问答；"
    "订单/工单/额度/天气/新闻请用工具，可忽略本段】"
)


def log_route(route: RouteResult) -> None:
    q = route.search_query or "（空→用原文）"
    print(
        f"（路由 intent={route.intent} need_rag={route.need_rag} "
        f"query={q} | {route.reason}）"
    )


def maybe_enrich(raw: str, *, route: RouteResult | None = None) -> str:
    """need_rag 且检索命中时附上下文；无命中/失败不硬塞空上下文。"""
    text = (raw or "").strip()
    if not text:
        return raw

    route = route or route_message(text)
    log_route(route)

    if not route.need_rag:
        return text

    query = (route.search_query or text).strip()
    try:
        hits = retrieve(query)
    except Exception as e:
        print(f"（知识库检索跳过：{e}）")
        return text

    if not hits:
        print("（知识库无命中，不附上下文）")
        return text

    print(f"（知识库命中 {len(hits)} 条）")
    context = format_hits_as_context(hits)
    return f"{text}\n\n{_RAG_HINT}\n{context}\n"
