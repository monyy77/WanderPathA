"""
state_graph/checkpointer.py

Durable checkpointing layer for state graphs (Final Project - Issue #1).
Owner: Person 1

Why this exists:
Without this, a state graph that pauses (e.g. waiting on an airline
webhook) loses everything if the process restarts. This module writes
the graph's full state to MySQL after every meaningful transition, so
a run can be killed and resumed from its last checkpoint with no lost
progress and no re-execution of completed steps.

Design choice: append-only log. Every save_checkpoint() call inserts a
NEW row rather than overwriting the previous one. load_checkpoint()
always returns the most recent row for a given run_id. This gives us:
  - a full audit trail of every transition (useful for the demo video
    and for debugging)
  - no risk of a partial UPDATE corrupting the only copy of the state
"""

import json
import os
from typing import Any, Optional

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def _get_connection():
    """Opens a new MySQL connection using credentials from .env.
    A fresh connection per call keeps this module safe to use from
    multiple graphs/processes without sharing connection state."""
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
    )


def save_checkpoint(
    run_id: str,
    graph_name: str,
    current_node: str,
    state: dict[str, Any],
    status: str = "running",
) -> int:
    """
    Persist the graph's full state after a meaningful transition.

    Args:
        run_id: unique identifier for this graph run.
        graph_name: which graph this belongs to, e.g. "flight_rebooking".
        current_node: the node the graph just finished/entered.
        state: the full state dict to persist. Must be JSON-serializable.
        status: "running" | "paused_hitl" | "failed" | "completed".

    Returns:
        The checkpoint_id of the newly inserted row.
    """
    try:
        state_json = json.dumps(state)
    except TypeError as e:
        raise TypeError(
            f"State for run_id={run_id} at node={current_node} is not "
            f"JSON-serializable: {e}"
        )

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO GraphCheckpoints
                (run_id, graph_name, current_node, state_json, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, graph_name, current_node, state_json, status),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def load_checkpoint(run_id: str) -> Optional[dict[str, Any]]:
    """
    Load the most recent checkpoint for a given run_id.
    Returns None if no checkpoint exists for this run_id.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT checkpoint_id, run_id, graph_name, current_node,
                   state_json, status, created_at
            FROM GraphCheckpoints
            WHERE run_id = %s
            ORDER BY created_at DESC, checkpoint_id DESC
            LIMIT 1
            """,
            (run_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        row["state"] = json.loads(row.pop("state_json"))
        return row
    finally:
        cursor.close()
        conn.close()


def load_history(run_id: str) -> list[dict[str, Any]]:
    """
    Load the FULL checkpoint history for a run, oldest first.
    Used for demo evidence and debugging.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT checkpoint_id, run_id, graph_name, current_node,
                   state_json, status, created_at
            FROM GraphCheckpoints
            WHERE run_id = %s
            ORDER BY created_at ASC, checkpoint_id ASC
            """,
            (run_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            row["state"] = json.loads(row.pop("state_json"))
        return rows
    finally:
        cursor.close()
        conn.close()