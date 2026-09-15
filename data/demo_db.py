# -*- coding: utf-8 -*-
"""演示业务库（SQLite）：订单 / 工单 / 账号额度。"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from rag import config

DB_PATH = config.PROJECT_ROOT / "data" / "demo_biz.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan TEXT NOT NULL,
    amount_yuan REAL NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    user_id TEXT PRIMARY KEY,
    plan TEXT NOT NULL,
    ai_quota_left INTEGER NOT NULL,
    api_quota_left INTEGER NOT NULL
);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
    return int(row["c"])


def init_db(*, reset: bool = False) -> Path:
    """reset=True 清空重灌；False 时若表为空则自动灌入演示数据。"""
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA)
        empty = _table_count(conn, "orders") == 0
        if reset or empty:
            conn.execute("DELETE FROM orders")
            conn.execute("DELETE FROM tickets")
            conn.execute("DELETE FROM accounts")
            conn.executemany(
                "INSERT INTO orders(order_id, user_id, plan, amount_yuan, status, updated_at) "
                "VALUES (?,?,?,?,?,?)",
                [
                    ("ORD001", "U001", "专业版", 199.0, "已发货", "2026-09-10"),
                    ("ORD002", "U001", "专业版", 199.0, "退款审核中", "2026-09-12"),
                    ("ORD003", "U002", "基础版", 99.0, "已完成", "2026-09-01"),
                    ("ORD004", "U003", "企业版", 0.0, "合同履约中", "2026-08-20"),
                ],
            )
            conn.executemany(
                "INSERT INTO tickets(ticket_id, user_id, title, status, updated_at) "
                "VALUES (?,?,?,?,?)",
                [
                    ("T001", "U001", "退款进度咨询", "处理中", "2026-09-13"),
                    ("T002", "U002", "发票抬头修改", "已关闭", "2026-09-05"),
                    ("T003", "U003", "SSO 开通申请", "处理中", "2026-09-11"),
                ],
            )
            conn.executemany(
                "INSERT INTO accounts(user_id, plan, ai_quota_left, api_quota_left) "
                "VALUES (?,?,?,?)",
                [
                    ("U001", "专业版", 1200, 35000),
                    ("U002", "基础版", 80, 500),
                    ("U003", "企业版", 999999, 999999),
                ],
            )
        conn.commit()
    finally:
        conn.close()
    return DB_PATH


def query_order(order_id: str) -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id.strip(),)
        ).fetchone()
        if not row:
            return f"未找到订单：{order_id}"
        return (
            f"订单 {row['order_id']}｜用户 {row['user_id']}｜套餐 {row['plan']}｜"
            f"金额 {row['amount_yuan']} 元｜状态 {row['status']}｜更新 {row['updated_at']}"
        )
    finally:
        conn.close()


def query_ticket(ticket_id: str) -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id.strip(),)
        ).fetchone()
        if not row:
            return f"未找到工单：{ticket_id}"
        return (
            f"工单 {row['ticket_id']}｜用户 {row['user_id']}｜"
            f"标题 {row['title']}｜状态 {row['status']}｜更新 {row['updated_at']}"
        )
    finally:
        conn.close()


def query_account(user_id: str) -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM accounts WHERE user_id = ?", (user_id.strip(),)
        ).fetchone()
        if not row:
            return f"未找到账号：{user_id}"
        return (
            f"账号 {row['user_id']}｜套餐 {row['plan']}｜"
            f"AI额度剩余 {row['ai_quota_left']}｜API额度剩余 {row['api_quota_left']}"
        )
    finally:
        conn.close()


def main() -> None:
    path = init_db(reset=True)
    print("SQLite ready:", path)
    print(query_order("ORD002"))
    print(query_ticket("T001"))
    print(query_account("U001"))


if __name__ == "__main__":
    main()
