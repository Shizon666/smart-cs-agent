# -*- coding: utf-8 -*-
"""
MCP Server：新闻搜索 / 舆情分析 / 邮件附件。
配置统一读仓库根目录 .env（从 Map_project 迁入的 SERPER/邮件/模型等）。
"""
from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import OpenAI

_PKG_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _PKG_DIR.parent
# 只使用仓库根 .env（与 app/rag 同一份）
load_dotenv(_ROOT_DIR / ".env", override=True)

_NEWS_DIR = _PKG_DIR / "google_news"
_REPORT_DIR = _PKG_DIR / "sentiment_reports"

mcp = FastMCP("NewsServer")


@mcp.tool()
async def search_google_news(keyword: str) -> str:
    """使用 Serper API 按关键词搜索新闻，返回前5条标题、描述和链接。"""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "❌ 未配置 SERPER_API_KEY，请在仓库根目录 .env 中设置（自 Map_project 迁入）"

    url = "https://google.serper.dev/news"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": keyword}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        data = response.json()

    if "news" not in data:
        return "❌ 未获取到搜索结果"

    articles = [
        {
            "title": item.get("title"),
            "desc": item.get("snippet"),
            "url": item.get("link"),
        }
        for item in data["news"][:5]
    ]

    _NEWS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"google_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_path = _NEWS_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    return (
        f"✅ 已获取与 [{keyword}] 相关的前5条 Google 新闻：\n"
        f"{json.dumps(articles, ensure_ascii=False, indent=2)}\n"
        f"📄 已保存到：{file_path}"
    )


@mcp.tool()
async def analyze_sentiment(text: str, filename: str) -> str:
    """对文本做情感/舆情分析，保存为 Markdown，返回文件路径。"""
    openai_key = os.getenv("DEEPSEEK_API_KEY")
    model = os.getenv("MODEL") or "deepseek-flash"
    base_url = os.getenv("BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")
    if not openai_key:
        return "❌ 未配置 DEEPSEEK_API_KEY（仓库根 .env）"
    if not base_url:
        return "❌ 未配置 BASE_URL（仓库根 .env）"

    client = OpenAI(api_key=openai_key, base_url=base_url)
    prompt = f"请对以下新闻内容进行情绪倾向分析，并说明原因：\n\n{text}"
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    result = (response.choices[0].message.content or "").strip()

    markdown = f"""# 舆情分析报告

**分析时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 原始文本

{text}

---

## 分析结果

{result}
"""

    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    file_path = _REPORT_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return str(file_path)


@mcp.tool()
async def send_email_with_attachment(
    to: str, subject: str, body: str, filename: str = ""
) -> str:
    """发送邮件；filename 可选（sentiment_reports 下文件名），有则加附件，无则只发正文。"""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    sender_email = os.getenv("EMAIL_USER")
    sender_pass = os.getenv("EMAIL_PASS")

    if not all([smtp_server, sender_email, sender_pass]):
        return "❌ 邮件配置不完整，请在仓库根 .env 设置 SMTP_SERVER / EMAIL_USER / EMAIL_PASS"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to
    msg.set_content(body)

    attach_note = "无附件"
    name = (filename or "").strip()
    if name:
        report_root = _REPORT_DIR.resolve()
        full_path = (report_root / name).resolve()
        if not str(full_path).startswith(str(report_root)):
            return "❌ 附件路径非法（仅允许 sentiment_reports 目录内文件）"
        if not full_path.exists():
            return f"❌ 附件路径无效，未找到文件: {full_path}"
        try:
            with open(full_path, "rb") as f:
                file_data = f.read()
            msg.add_attachment(
                file_data,
                maintype="application",
                subtype="octet-stream",
                filename=full_path.name,
            )
            attach_note = f"附件: {full_path.name}"
        except Exception as e:
            return f"❌ 附件读取失败: {e}"

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_pass)
            server.send_message(msg)
        return f"✅ 邮件已成功发送给 {to}（{attach_note}）"
    except Exception as e:
        return f"❌ 邮件发送失败: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
