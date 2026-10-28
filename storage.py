"""Saves and loads prompt history using SQLite (built into Python).

The database file path comes from config.get_db_path() (DB_PATH in .env).
"""

import csv
import io
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import config

COLUMNS = ["id", "created_at", "mode", "original", "optimized", "explanation"]


@contextmanager
def _connect(db_path: str | None):
    """Open a connection (default path from config), save changes, and always close it."""
    conn = sqlite3.connect(db_path or config.get_db_path())
    conn.row_factory = sqlite3.Row  # rows can be read like dicts
    try:
        with conn:  # commits on success, rolls back on error
            yield conn
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    """Create the history table if it does not exist yet."""
    with _connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                original TEXT NOT NULL,
                optimized TEXT NOT NULL,
                explanation TEXT NOT NULL
            )"""
        )


def save_entry(mode, original, optimized, explanation, db_path: str | None = None) -> int:
    """Insert one optimization into history and return its id."""
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO history (created_at, mode, original, optimized, explanation) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), mode, original, optimized, explanation),
        )
        return cur.lastrowid


def load_history(limit: int | None = config.HISTORY_LIMIT, db_path: str | None = None) -> list[dict]:
    """Return the latest `limit` entries, newest first (limit=None returns all)."""
    init_db(db_path)
    sql = "SELECT * FROM history ORDER BY id DESC"
    params: tuple = ()
    if limit is not None:
        sql += " LIMIT ?"
        params = (limit,)
    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def delete_entry(entry_id: int, db_path: str | None = None) -> None:
    """Delete a single history entry by id (does nothing if it does not exist)."""
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))


def clear_history(db_path: str | None = None) -> None:
    """Delete ALL history entries."""
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM history")


def export_json(db_path: str | None = None) -> str:
    """Return the whole history as a JSON string."""
    return json.dumps(load_history(None, db_path), ensure_ascii=False, indent=2)


def export_csv(db_path: str | None = None) -> str:
    """Return the whole history as CSV text (with a header row)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(load_history(None, db_path))
    return buffer.getvalue()
