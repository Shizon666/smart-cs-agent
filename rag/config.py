# -*- coding: utf-8 -*-
"""RAG / Milvus / Embedding 配置。"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Milvus（可用环境变量覆盖）
MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
DB_NAME = "smart_cs"
COLLECTION_NAME = "knowledge_docs"

# 语料：优先扫描 raw 多格式目录；保留单文件兼容
KNOWLEDGE_RAW_DIR = PROJECT_ROOT / "knowledge" / "raw"
KNOWLEDGE_FILE = PROJECT_ROOT / "knowledge" / "knowledge.txt"

# SiliconFlow 免费档 BGE-M3
EMBED_MODEL_NAME = "BAAI/bge-m3"
EMBED_DIM = 1024

CHUNK_SIZE = 200
CHUNK_OVERLAP = 80
SEPARATORS = [
    "\n==============================\n",
    "\n\n",
    "\n",
    "。",
    " ",
    "",
]

DEFAULT_TOP_K = 5
MIN_SCORE = 0.35
