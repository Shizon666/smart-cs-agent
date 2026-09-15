# smart-cs-agent

智能客服 Agent：多格式文档 RAG + SQLite 业务查询 + 天气 Tool + MCP。

## 准备

```bash
cd D:\Code\smart-cs-agent
uv sync
# 根目录 .env（含 Map_project 迁入的 MCP 配置）
# Docker Milvus → localhost:19530
```

## 使用

```bash
# 1) 初始化业务库
uv run python -m data.demo_db

# 2) 向量入库（语料在 knowledge/raw/<类型>/）
uv run python -m rag.ingest --recreate

# 3) 终端多轮（先路由再按需 RAG；同进程短期记忆；助手流式输出）
uv run python -m app.main --no-mcp
# 或：PyCharm 打开 app/main.py → Run（Working directory=仓库根；Parameters 可填 --no-mcp）
# /exit 退出；/help 帮助；/clear 清空会话记忆（换新 thread）
# 记忆：InMemorySaver，关终端即丢；不是用户画像，也不是知识库
# 流式：最终答复逐块打印；工具调用前有一行「调用工具」提示
# 发信：启用 MCP 时，send_email 前会要求 y/N 确认；--no-mcp 无此工具
# 摘要：消息过多时自动压缩旧轮次（SUM_TRIGGER_MESSAGES / SUM_KEEP_MESSAGES，默认 12/6）
# 重试：模型/工具瞬时失败有限次退避（RETRY_MAX_RETRIES，默认 2；0=关闭）
# 长期记忆：配置 STORE_POSTGRES_URI 后挂 PostgresStore；姓名跨会话；/clear 只清短期
```


## 数据说明

| 类型 | 位置 | 用途 |
|------|------|------|
| 多格式文档 | `knowledge/raw/`（md/txt/html/docx） | RAG → Milvus |
| 结构化业务 | `data/demo_biz.db`（SQLite 演示） | Tool 查订单/工单/额度 |
| 配置 | 根目录 `.env` | App / RAG / MCP 统一 |

## 结构

```text
app/          入口 + Agent
rag/          loaders / embeddings / vectorstore / ingest / retrieve
tools/        weather + biz_query
mcp_server/   MCP Server
knowledge/    语料 + raw/
data/         SQLite 演示库
docs/         工程文档
```
