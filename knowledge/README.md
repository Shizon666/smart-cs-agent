# knowledge — 语料

`raw/` 下**按格式分子目录**（对齐教程 asset/load 类型）：

```text
knowledge/raw/
  md/      *.md
  txt/     *.txt
  html/    *.html
  csv/     *.csv
  pdf/     *.pdf
  json/    *.json
  docx/    *.docx
```

向对应类型目录放入文件后入库：

```bash
uv run python -m rag.ingest --recreate
```

`rag/loaders.py` 使用 `rglob` 递归扫描上述子目录。
