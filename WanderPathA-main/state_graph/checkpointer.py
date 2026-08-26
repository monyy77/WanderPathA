"""
state_graph/checkpointer.py

Durable MySQL checkpoint layer for LangGraph state graphs.
"""

import json
import os
from typing import Any, Optional

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def _get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3307)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "travel_agency"),
    )


def _ensure_table():
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS GraphCheckpoints (
            checkpoint_id INT AUTO_INCREMENT PRIMARY KEY,
            run_id VARCHAR(255) NOT NULL,
            graph_name VARCHAR(255) NOT NULL,
            current_node VARCHAR(255) NOT NULL,
            state_json LONGTEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    cursor.close()
    conn.close()


def save_checkpoint(
    run_id: str,
    graph_name: str,
    current_node: str,
    state: dict[str, Any],
    status: str = "running",
) -> int:

    _ensure_table()

    state_json = json.dumps(
        state,
        default=str,
        ensure_ascii=False
    )

    conn = _get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO GraphCheckpoints
            (
                run_id,
                graph_name,
                current_node,
                state_json,
                status
            )
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                run_id,
                graph_name,
                current_node,
                state_json,
                status,
            ),
        )

        conn.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        conn.close()


def load_checkpoint(run_id: str) -> Optional[dict[str, Any]]:

    _ensure_table()

    conn = _get_connection()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM GraphCheckpoints
            WHERE run_id=%s
            ORDER BY checkpoint_id DESC
            LIMIT 1
            """,
            (run_id,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        row["state"] = json.loads(
            row["state_json"]
        )

        return row

    finally:
        cursor.close()
        conn.close()


def load_history(run_id: str) -> list[dict[str, Any]]:

    _ensure_table()

    conn = _get_connection()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM GraphCheckpoints
            WHERE run_id=%s
            ORDER BY checkpoint_id ASC
            """,
            (run_id,),
        )

        rows = cursor.fetchall()

        for row in rows:
            row["state"] = json.loads(
                row["state_json"]
            )

        return rows

    finally:
        cursor.close()
        conn.close()


def complete_checkpoint(
    run_id: str,
    graph_name: str,
    current_node: str,
    state: dict[str, Any],
):

    return save_checkpoint(
        run_id=run_id,
        graph_name=graph_name,
        current_node=current_node,
        state=state,
        status="completed",
    )