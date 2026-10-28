"""Saves and loads prompt history using SQLite (built into Python)."""

import sqlite3
from datetime import datetime

DB_PATH = "history.db"


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a connection; rows can be read like dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
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


def save_entry(mode, original, optimized, explanation, db_path: str = DB_PATH) -> int:
    """Insert one optimization into history and return its id."""
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO history (created_at, mode, original, optimized, explanation) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), mode, original, optimized, explanation),
        )
        return cur.lastrowid


def load_history(limit: int = 20, db_path: str = DB_PATH) -> list[dict]:
    """Return the latest `limit` entries, newest first."""
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
