# 智能客服多能力助手（Smart CS Agent）

面向客服/顾问场景的多轮 Agent：知识库问答（RAG）、订单/工单查询、天气与 MCP 外部工具统一调度，并对发信等高危操作做人工确认（HITL）。

## 技术栈
LangChain / LangGraph · RAG（BGE-M3 + Milvus）· FastMCP · SQLite / Postgres Store

## 核心能力
- 意图路由：规则优先 + LLM 补判
- Tool Calling：本地业务查询 + MCP 工具
- 会话治理：短期记忆、摘要、可选长期画像
- 安全：敏感工具 HITL 确认

## 快速开始
（写：环境变量、安装、启动命令）
