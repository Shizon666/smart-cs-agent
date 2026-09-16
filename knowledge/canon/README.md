# knowledge/canon — 业务知识真源（Phase 1）

本目录为 **唯一业务口径真源**（产品名：**智答云**）。

| 文件 | 说明 |
|------|------|
| `_numbers.md` | 黄金数字表（改数前全局核对；可不入库） |
| `00`～`09_*.md` | 十主题正文 |
| `10_典型客服问答.json` | FAQ 35 条 |

设计与后续 Phase（派生 raw / 调 chunk）：见  
[`docs/smart-cs-agent-业务知识库与RAG调优设计文档.md`](../../docs/smart-cs-agent-业务知识库与RAG调优设计文档.md)

> Phase 1～2 已完成：canon 真源 + raw 多格式派生。  
> 改口径只改 `canon/`，再跑：`uv run python -m knowledge.export_raw`
