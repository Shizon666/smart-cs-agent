# knowledge — 语料

> **真源**：[`canon/`](canon/)（智答云 · A 档）  
> **派生入库**：[`raw/`](raw/)（由 canon 导出，供 `rag.ingest` 扫描）  
> **设计**：[`docs/smart-cs-agent-业务知识库与RAG调优设计文档.md`](../docs/smart-cs-agent-业务知识库与RAG调优设计文档.md)

## 目录

```text
knowledge/
  canon/          # 唯一业务口径（改内容只改这里）
  raw/            # ingest 入口（多格式演示）
    md/ txt/ html/ csv/ json/ pdf/ docx/
  knowledge.txt   # T1：仅入口说明，不再当第二真源
  export_raw.py   # canon → raw 派生脚本
```

## 命令

```bash
# 修改 canon 后重新派生 raw
uv run python -m knowledge.export_raw

# 写入 Milvus（需服务可用）
uv run python -m rag.ingest --recreate
```

`rag/loaders.py` 使用 `rglob` 递归扫描 `raw/` 下支持的后缀。
