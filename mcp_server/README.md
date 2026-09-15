# mcp_server — MCP 工具进程（进程外）

通过 MCP（stdio）提供新闻 / 舆情 / 邮件。由 `app` 连接；**不是聊天入口**。

| 文件 | 职责 |
|------|------|
| `server.py` | FastMCP 工具实现 |
| `loader.py` | 供 app 加载 MCP tools；失败返回 [] |

## 配置（重要）

**统一使用仓库根目录 `.env`**（从 `D:\Code\Map_project\.env` 迁入 MCP 相关项）。  
本目录**不单独维护**业务密钥 `.env`。

| 变量 | 工具 |
|------|------|
| `SERPER_API_KEY` | search_google_news |
| `DEEPSEEK_API_KEY` / `BASE_URL` / `MODEL` | analyze_sentiment |
| `SMTP_*` / `EMAIL_*` | send_email_with_attachment |

## 产物

- `mcp_server/google_news/`
- `mcp_server/sentiment_reports/`
