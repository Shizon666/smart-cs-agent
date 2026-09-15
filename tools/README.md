# tools — 本地工具（进程内）

Agent 直接注册的同步/异步小工具；不启动 MCP 子进程。

| 文件 | 职责 |
|------|------|
| `weather.py` | `get_weather`，Open-Meteo，免 API Key |
| `biz_query.py` | `lookup_order` / `lookup_ticket` / `lookup_account`（SQLite） |
| `profile.py` | `save_user_info` / `get_user_info`（LangGraph Store 画像） |

**约定：** 工具函数名英文；`description` 可中文，写清何时调用。  
**后续：** 若再增加计算器等，仍放本目录，保持「本地、轻量」。
