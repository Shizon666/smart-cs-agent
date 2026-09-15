# rag — 知识库 RAG

切分、向量化、Milvus、检索。与 MCP / 天气无关。

| 文件 | 职责 |
|------|------|
| `config.py` | URI、库名、切分参数、模型名、`KNOWLEDGE_RAW_DIR` |
| `embeddings.py` | Embedding 工厂（BGE-M3） |
| `vectorstore.py` | Milvus 连接与 collection |
| `loaders.py` | 多格式：txt/md/html/docx/**pdf/csv/json**（对齐 asset/load） |
| `ingest.py` | 扫 raw → 切分 → 入库 |
| `retrieve.py` | `retrieve(query)` + 上下文格式化 |

**不要**命名为 `client.py`（避免与 MCP 入口混淆）。

```bash
uv run python -m rag.ingest
uv run python -m rag.ingest --recreate
```
