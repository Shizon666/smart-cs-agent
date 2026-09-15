# -*- coding: utf-8 -*-
"""知识库：多格式加载 → 切分 → Embedding → 写入 Milvus。"""
from __future__ import annotations

import argparse

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag import config
from rag.embeddings import get_embed_model
from rag.loaders import load_raw_documents
from rag.vectorstore import ensure_collection, get_milvus_client


def load_and_split():
    if config.KNOWLEDGE_RAW_DIR.exists() and any(config.KNOWLEDGE_RAW_DIR.iterdir()):
        print(f"从目录加载：{config.KNOWLEDGE_RAW_DIR}")
        documents = load_raw_documents(config.KNOWLEDGE_RAW_DIR)
    elif config.KNOWLEDGE_FILE.exists():
        print(f"回退单文件：{config.KNOWLEDGE_FILE}")
        documents = TextLoader(
            file_path=str(config.KNOWLEDGE_FILE), encoding="utf-8"
        ).load()
        for d in documents:
            d.metadata = {
                **(d.metadata or {}),
                "source": str(config.KNOWLEDGE_FILE),
                "filename": config.KNOWLEDGE_FILE.name,
                "filetype": "txt",
            }
    else:
        raise FileNotFoundError(
            f"未找到语料：请准备 {config.KNOWLEDGE_RAW_DIR} 或 {config.KNOWLEDGE_FILE}"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=config.SEPARATORS,
    )
    return splitter.split_documents(documents)


def ingest_knowledge(*, recreate: bool = False) -> int:
    client = get_milvus_client()
    ensure_collection(client, recreate=recreate)

    chunks = load_and_split()
    print(f"文档共切分为 {len(chunks)} 个 chunk")

    embed_model = get_embed_model()
    texts = [c.page_content for c in chunks]
    vectors = embed_model.embed_documents(texts)

    data = [
        {
            "id": i,
            "vector": vectors[i],
            "text": chunks[i].page_content,
            "source": str(chunks[i].metadata.get("source", "")),
            "chunk_id": i,
        }
        for i in range(len(chunks))
    ]

    insert_res = client.upsert(collection_name=config.COLLECTION_NAME, data=data)
    client.flush(collection_name=config.COLLECTION_NAME)
    stats = client.get_collection_stats(collection_name=config.COLLECTION_NAME)

    print("insert results:", insert_res)
    print("collection stats:", stats)
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="多格式知识库写入 Milvus")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="删除并重建 collection 后再入库",
    )
    args = parser.parse_args()
    n = ingest_knowledge(recreate=args.recreate)
    print(f"完成，共写入 {n} 条")


if __name__ == "__main__":
    main()
