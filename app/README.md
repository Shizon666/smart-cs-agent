# app — 应用层

终端多轮对话入口与单 Agent 调度。

| 文件 | 职责 |
|------|------|
| `main.py` | CLI：终端多轮；`thread_id` + 流式 + `--no-mcp`；Store 启动探测（超时降级，非 Agent 重试） |
| `chat.py` | REPL（`/exit` `/help` `/clear`；前缀 `助手:` 后由 reply 流式打正文） |
| `routing.py` | 意图路由 + 按需检索拼装 |
| `agent.py` | `create_agent`：Checkpointer + 可选 Store + 摘要 + 重试；MCP 经 HITL |
| `hitl.py` | 发信前 CLI `y/N` 确认 |
| `prompts.py` | `SYSTEM_PROMPT` / `ROUTE_SYSTEM_PROMPT` / `SUMMARY_PROMPT` |

**依赖方向：** 可引用 `rag`、`tools`、`mcp_server`。  
**不要：** 在这里写 Embedding / Milvus / SMTP 实现细节；不要把 RAG/业务库称作会话记忆。

```bash
uv run python -m app.main --no-mcp
# /clear 换新 thread_id，清空短期记忆
```

