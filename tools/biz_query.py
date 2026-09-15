# -*- coding: utf-8 -*-
"""结构化业务查询 Tool（SQLite 演示库）。"""
from __future__ import annotations

from langchain.tools import tool

from data.demo_db import init_db, query_account, query_order, query_ticket

init_db(reset=False)


@tool
def lookup_order(order_id: str) -> str:
    """根据订单号查询订单状态、套餐与金额。订单号形如 ORD001。

    Args:
        order_id: 订单号，例如 ORD001、ORD002
    """
    return query_order(order_id)


@tool
def lookup_ticket(ticket_id: str) -> str:
    """根据工单号查询工单标题与处理状态。工单号形如 T001。

    Args:
        ticket_id: 工单号，例如 T001
    """
    return query_ticket(ticket_id)


@tool
def lookup_account(user_id: str) -> str:
    """根据用户 ID 查询套餐与剩余额度。用户 ID 形如 U001。

    Args:
        user_id: 用户 ID，例如 U001
    """
    return query_account(user_id)
