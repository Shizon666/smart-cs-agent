# -*- coding: utf-8 -*-
"""向量检索。"""
from __future__ import annotations

from typing import Any

from rag import config
from rag.embeddings import get_embed_model
from rag.vectorstore import get_milvus_client


def retrieve(query: str, limit: int = config.DEFAULT_TOP_K) -> list[dict[str, Any]]:
    """按自然语言问题检索；必须传 query 字符串。"""
    if not isinstance(query, str) or not query.strip():
        return []

    embed_model = get_embed_model()
    client = get_milvus_client()
    query_vector = embed_model.embed_query(query.strip())

    results = client.search(
        collection_name=config.COLLECTION_NAME,
        data=[query_vector],
        limit=limit,
        output_fields=["text", "chunk_id", "source"],
    )
    hits = results[0] if results else []

    return [h for h in hits if h.get("distance", 0) >= config.MIN_SCORE]


def format_hits_as_context(hits: list[dict[str, Any]]) -> str:
    blocks = []
    for i, hit in enumerate(hits, 1):
        entity = hit.get("entity") or {}
        text = entity.get("text", "")
        source = entity.get("source", "unknown")
        chunk_id = entity.get("chunk_id", "unknown")
        blocks.append(f"[片段{i} | chunk_id={chunk_id} | source={source}]\n{text}")
    return "\n\n".join(blocks)
