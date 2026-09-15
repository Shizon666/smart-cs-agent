# -*- coding: utf-8 -*-
"""Embedding 模型工厂。"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.embeddings import init_embeddings

from rag import config

load_dotenv(override=True)


def get_embed_model():
    api_key = os.getenv("SILICONFLOW_API_KEY")
    base_url = os.getenv("SILICONFLOW_BASE_URL")
    if not api_key:
        raise ValueError("未配置 SILICONFLOW_API_KEY，请在 .env 中填写")
    return init_embeddings(
        model="openai:" + config.EMBED_MODEL_NAME,
        api_key=api_key,
        base_url=base_url,
    )
