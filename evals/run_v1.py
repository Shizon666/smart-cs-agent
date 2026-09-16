# -*- coding: utf-8 -*-
"""
按 cases_v1.csv 批量跑题并回写打分列（evals → app | rag）。

用法（仓库根）：
  uv run python -m evals.run_v1 --no-mcp
  uv run python -m evals.run_v1 --no-mcp --limit 3
  uv run python -m evals.run_v1 --no-mcp --ids E21,E28,E29

开 LANGSMITH_TRACING 时，每题一条独立根 Trace（每题新 thread_id，等价 /clear）。
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env", override=True)

# 与 cases_v1.csv / 设计文档契约一致；勿擅自改名
_CSV_FIELDS = [
    "id",
    "question",
    "intent",
    "need_rag",
    "expect_tool",
    "gold_keywords",
    "source",
    "optional",
    "route_ok",
    "rag_hit",
    "grounded",
    "tool_ok",
    "latency_ms",
    "notes",
]

_DEFAULT_CSV = _ROOT / "evals" / "cases_v1.csv"
_EVAL_TAG = "eval-v1"


def _chunk_text(chunk: Any) -> str:
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


def _parse_bool(raw: str) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "y"}


def _keyword_groups(raw: str) -> list[str]:
    return [p.strip() for p in (raw or "").split("|") if p.strip()]


def _any_keyword_hit(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return False
    hay = text or ""
    return any(k in hay for k in keywords)


def _score_route(
    *,
    expect_intent: str,
    expect_need_rag: bool,
    actual_intent: str,
    actual_need_rag: bool,
) -> tuple[str, str]:
    """返回 (route_ok, note)。unknown↔knowledge 且 need_rag=true 记 partial。"""
    ei = (expect_intent or "").strip().lower()
    ai = (actual_intent or "").strip().lower()
    need_ok = actual_need_rag == expect_need_rag
    if ai == ei and need_ok:
        return "true", ""
    if (
        need_ok
        and expect_need_rag
        and {ei, ai} <= {"knowledge", "unknown"}
        and ei != ai
    ):
        return "partial", f"intent {ai}≈{ei}"
    bits = []
    if ai != ei:
        bits.append(f"intent {ai}!={ei}")
    if not need_ok:
        bits.append(f"need_rag {actual_need_rag}!={expect_need_rag}")
    return "false", "; ".join(bits)


def _score_tool(expect_tool: str, used: list[str]) -> str:
    expect = (expect_tool or "").strip()
    if not expect:
        return ""
    return "true" if expect in used else "false"


async def _run_one(
    agent,
    *,
    case_id: str,
    question: str,
    route,
) -> tuple[str, list[str], int]:
    """返回 (answer, tool_names, latency_ms)。"""
    from app.routing import maybe_enrich

    t0 = time.perf_counter()
    content = maybe_enrich(question, route=route)
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": thread_id},
        "tags": [_EVAL_TAG, case_id],
        "metadata": {"eval": _EVAL_TAG, "case_id": case_id},
    }
    payload = {"messages": [{"role": "user", "content": content}]}
    parts: list[str] = []
    tools: list[str] = []
    async for ev in agent.astream_events(payload, config=config, version="v2"):
        kind = ev.get("event")
        if kind == "on_tool_start":
            name = ev.get("name") or "tool"
            tools.append(str(name))
            continue
        if kind != "on_chat_model_stream":
            continue
        piece = _chunk_text((ev.get("data") or {}).get("chunk"))
        if piece:
            parts.append(piece)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return "".join(parts).strip(), tools, latency_ms


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit(f"CSV 无表头: {path}")
        missing = [c for c in _CSV_FIELDS if c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"CSV 缺列 {missing}；契约列为 {_CSV_FIELDS}")
        return [{k: (row.get(k) or "") for k in _CSV_FIELDS} for row in reader]


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _print_table(rows: list[dict[str, str]]) -> None:
    cols = [
        "id",
        "route_ok",
        "rag_hit",
        "grounded",
        "tool_ok",
        "latency_ms",
        "notes",
    ]
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    print("\n" + header)
    print("-+-".join("-" * widths[c] for c in cols))
    for r in rows:
        print(" | ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))


def _summarize(rows: list[dict[str, str]]) -> None:
    def rate(field: str) -> str:
        vals = [r[field] for r in rows if r.get(field) in {"true", "false", "partial"}]
        if not vals:
            return "n/a"
        score = sum(
            1.0 if v == "true" else 0.5 if v == "partial" else 0.0 for v in vals
        )
        return f"{score / len(vals) * 100:.1f}% ({score:g}/{len(vals)})"

    latencies = [
        int(r["latency_ms"])
        for r in rows
        if str(r.get("latency_ms") or "").isdigit()
    ]
    p50 = p95 = "n/a"
    if latencies:
        ordered = sorted(latencies)
        p50 = f"{ordered[len(ordered) // 2]}ms"
        p95 = f"{ordered[max(0, int(len(ordered) * 0.95) - 1)]}ms"

    print("\n=== 汇总 ===")
    print(f"route_ok : {rate('route_ok')}")
    print(f"rag_hit  : {rate('rag_hit')}")
    print(f"grounded : {rate('grounded')}")
    print(f"tool_ok  : {rate('tool_ok')}")
    print(f"latency  : P50={p50}  P95={p95}（本机脚本计时；可对照 LangSmith）")


async def _run_selected(
    agent,
    selected: list[dict[str, str]],
    *,
    route_message,
    retrieve,
) -> None:
    for i, row in enumerate(selected, 1):
        qid = row["id"]
        question = row["question"]
        print(f"\n[{i}/{len(selected)}] {qid} {question}")
        notes: list[str] = []
        try:
            route = route_message(question)
            answer, tools, latency_ms = await _run_one(
                agent, case_id=qid, question=question, route=route
            )
        except Exception as e:
            row["route_ok"] = "false"
            row["rag_hit"] = ""
            row["grounded"] = ""
            row["tool_ok"] = "false" if row["expect_tool"].strip() else ""
            row["latency_ms"] = ""
            row["notes"] = f"error:{e}"
            print(f"  FAIL: {e}")
            continue

        expect_need = _parse_bool(row["need_rag"])
        route_ok, route_note = _score_route(
            expect_intent=row["intent"],
            expect_need_rag=expect_need,
            actual_intent=route.intent,
            actual_need_rag=route.need_rag,
        )
        if route_note:
            notes.append(route_note)

        keywords = _keyword_groups(row["gold_keywords"])
        rag_hit = ""
        grounded = ""
        if expect_need and keywords:
            try:
                query = (route.search_query or question).strip()
                hits = retrieve(query)
                blob = "\n".join(
                    str((h.get("entity") or {}).get("text") or "") for h in hits
                )
                rag_hit = "true" if _any_keyword_hit(blob, keywords) else "false"
            except Exception as e:
                rag_hit = "false"
                notes.append(f"retrieve:{e}")
            grounded = "true" if _any_keyword_hit(answer, keywords) else "false"
        elif keywords:
            grounded = "true" if _any_keyword_hit(answer, keywords) else "false"

        tool_ok = _score_tool(row["expect_tool"], tools)
        if row["expect_tool"].strip() and tool_ok == "false":
            notes.append(f"tools={tools or []}")

        row["route_ok"] = route_ok
        row["rag_hit"] = rag_hit
        row["grounded"] = grounded
        row["tool_ok"] = tool_ok
        row["latency_ms"] = str(latency_ms)
        row["notes"] = "; ".join(notes)
        preview = answer.replace("\n", " ")[:80]
        print(
            f"  route={route.intent}/{route.need_rag} ok={route_ok} "
            f"rag={rag_hit or '-'} grounded={grounded or '-'} "
            f"tool={tool_ok or '-'} {latency_ms}ms"
        )
        print(f"  answer: {preview}{'…' if len(answer) > 80 else ''}")


def main() -> None:
    parser = argparse.ArgumentParser(description="sca evals v1 批量跑题")
    parser.add_argument(
        "--csv",
        type=Path,
        default=_DEFAULT_CSV,
        help="题集路径（默认 evals/cases_v1.csv）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="结果写出路径（默认覆盖 --csv）",
    )
    parser.add_argument("--limit", type=int, default=0, help="最多跑 N 题（0=全部）")
    parser.add_argument(
        "--ids",
        type=str,
        default="",
        help="只跑指定 id，逗号分隔，如 E01,E21",
    )
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="包含 optional=true（E35/E36，常需 MCP/HITL）",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="不加载 MCP（推荐 E01～E34）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只列出将跑的题，不调用模型",
    )
    args = parser.parse_args()

    csv_path = args.csv if args.csv.is_absolute() else _ROOT / args.csv
    out_path = args.out or csv_path
    if args.out and not out_path.is_absolute():
        out_path = _ROOT / args.out

    rows = _load_rows(csv_path)
    id_filter = {x.strip() for x in args.ids.split(",") if x.strip()}

    selected: list[dict[str, str]] = []
    for row in rows:
        if id_filter and row["id"] not in id_filter:
            continue
        if not args.include_optional and _parse_bool(row["optional"]):
            continue
        selected.append(row)
        if args.limit and len(selected) >= args.limit:
            break

    if not selected:
        raise SystemExit("没有选中任何题目（检查 --ids / --include-optional / --limit）")

    print(f"将跑 {len(selected)} 题 → {out_path}")
    tracing = (os.getenv("LANGSMITH_TRACING") or "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    print(
        f"LangSmith tracing: {'on' if tracing else 'off'}；"
        f"tag={_EVAL_TAG}（每题新 thread）"
    )
    if args.dry_run:
        for r in selected:
            print(f"  {r['id']}: {r['question']}")
        return

    # 延迟导入，避免 dry-run 也拉起模型依赖
    from app.agent import build_agent
    from app.routing import route_message
    from rag.retrieve import retrieve

    agent = build_agent(enable_mcp=not args.no_mcp, store=None)
    asyncio.run(
        _run_selected(
            agent,
            selected,
            route_message=route_message,
            retrieve=retrieve,
        )
    )

    # 把结果合并回全表（未跑的题保留原值）
    by_id = {r["id"]: r for r in rows}
    for r in selected:
        by_id[r["id"]] = r
    merged = [by_id[r["id"]] for r in rows]
    _write_rows(out_path, merged)
    _print_table(selected)
    _summarize(selected)
    print(f"\n已写入: {out_path}")
    print(
        "LangSmith: 每题 1 条根 Trace；可用 tag "
        f"`{_EVAL_TAG}` 过滤。/clear 本身不上报。"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已中断。", file=sys.stderr)
        raise SystemExit(130) from None
