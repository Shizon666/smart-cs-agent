# evals — 评测题集与跑分

依赖方向：`evals → app | rag`（不被业务包反向引用）。见
[`docs/02-开发标准/结构与模块.md`](../docs/02-开发标准/结构与模块.md)。

题集与打分口径：
[`docs/smart-cs-agent-LangSmith评测量化设计文档.md`](../docs/smart-cs-agent-LangSmith评测量化设计文档.md)

| 文件 | 说明 |
|------|------|
| `cases_v1.csv` | v1 共 36 条；`optional=true` 的 E35/E36 依赖 MCP 环境 |
| `run_v1.py` | 批量跑题、回写打分列、终端汇总表；开 LangSmith 时每题独立 Trace |

## 怎么跑

```bash
# 推荐：E01～E34，不加载 MCP
uv run python -m evals.run_v1 --no-mcp

# 先试 3 题 / 指定 id
uv run python -m evals.run_v1 --no-mcp --limit 3
uv run python -m evals.run_v1 --no-mcp --ids E21,E28,E29

# 另存结果，不覆盖题集
uv run python -m evals.run_v1 --no-mcp --out evals/results_v1.csv

# 只看将跑哪些题
uv run python -m evals.run_v1 --dry-run
```

默认回写 `cases_v1.csv` 打分列；建议先 `--out` 另存。

## CSV 列（契约，勿改名）

期望：`id, question, intent, need_rag, expect_tool, gold_keywords, source, optional`  
实测：`route_ok, rag_hit, grounded, tool_ok, latency_ms, notes`  
（`route_ok` 可为 `true` / `false` / `partial`）

## 边界

- `grounded` / `rag_hit` 按 `gold_keywords` 关键词半自动；Fail 建议人工复核。
- 每题新 `thread_id`（等价 `/clear`）；LangSmith 上是多条 Trace，不是一条。
- Trace tag：`eval-v1` + 题号（如 `E21`），便于控制台过滤。
