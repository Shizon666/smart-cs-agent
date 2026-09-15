# -*- coding: utf-8 -*-
"""终端多轮 REPL：可聊、可退出；短期记忆下支持 /clear；助手回复由 reply 流式打出。"""
from __future__ import annotations

from collections.abc import Callable


def run_repl(
    reply: Callable[[str], str],
    *,
    on_clear: Callable[[], None] | None = None,
) -> None:
    """
    reply(user_text) -> 助手最终文本（实现侧应向 stdout 流式打印正文）。
    on_clear：清空短期记忆（通常换新 thread_id）；未传则 /clear 提示未启用。
    命令：/exit 退出；/help 帮助；/clear 清空会话。
    """
    print("进入多轮对话（E1：先路由，按需查知识库；同进程短期记忆；助手流式输出）。")
    print("命令：/exit 退出，/help 帮助，/clear 清空会话。")
    while True:
        try:
            raw = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已结束。")
            return
        if not raw:
            continue
        if raw in {"/exit", "/quit", "/q"}:
            print("已结束。")
            return
        if raw == "/help":
            print("/exit  退出（亦可用 /quit、/q）")
            print("/help  本说明")
            print("/clear 清空会话短期记忆（换新 thread；关终端也会丢）")
            print("说明：先意图路由；政策类会查知识库；订单/天气走工具。")
            print("记忆：短期=同进程同会话（/clear 清空）；长期=姓名画像（Store，/clear 不清）。")
            print("输出：助手回复流式打印；调用工具时会有一行提示。")
            print("安全：发邮件前会要求 y/N 确认（需启用 MCP）。")
            continue
        if raw == "/clear":
            if on_clear is None:
                print("（/clear 未启用）")
            else:
                on_clear()
                print("已清空会话记忆（新 thread）。")
            continue

        try:
            print("助手: ", end="", flush=True)
            reply(raw)
            print()
        except Exception as e:
            print(f"\n助手: （本轮失败）{e}")
            continue
