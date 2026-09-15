# -*- coding: utf-8 -*-
"""Milvus VectorStore：连接、库与 collection 管理。"""
from __future__ import annotations

from pymilvus import MilvusClient

from rag import config


def get_milvus_client(*, ensure_db: bool = True) -> MilvusClient:
    client = MilvusClient(config.MILVUS_URI)
    if ensure_db:
        existed = client.list_databases()
        if config.DB_NAME not in existed:
            client.create_database(db_name=config.DB_NAME)
        client.use_database(db_name=config.DB_NAME)
    return client


def ensure_collection(client: MilvusClient, *, recreate: bool = False) -> None:
    """默认不存在才创建；recreate=True 时删除重建。"""
    has = client.has_collection(collection_name=config.COLLECTION_NAME)
    if has and recreate:
        client.drop_collection(collection_name=config.COLLECTION_NAME)
        has = False
    if not has:
        client.create_collection(
            collection_name=config.COLLECTION_NAME,
            dimension=config.EMBED_DIM,
            metric_type="COSINE",
        )
