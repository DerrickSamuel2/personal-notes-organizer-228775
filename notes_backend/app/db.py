"""
SQLite access layer.

We intentionally use the stdlib sqlite3 module to match the provided SQLite schema
and keep the backend lightweight.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List, Optional


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    """Convert sqlite rows into dicts keyed by column name."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# PUBLIC_INTERFACE
def create_connection(db_path: str) -> sqlite3.Connection:
    """Create a SQLite connection configured for this application.

    Args:
        db_path: Filesystem path to the sqlite database file.

    Returns:
        sqlite3.Connection: Configured connection.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = _dict_factory
    # Align with init_db.py expectations.
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


@contextmanager
def get_conn(db_path: str) -> Iterator[sqlite3.Connection]:
    """Context manager yielding a connection and ensuring close."""
    conn = create_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def fetch_one(
    conn: sqlite3.Connection, query: str, params: Iterable[Any] = ()
) -> Optional[Dict[str, Any]]:
    cur = conn.execute(query, tuple(params))
    row = cur.fetchone()
    return row if row is not None else None


def fetch_all(
    conn: sqlite3.Connection, query: str, params: Iterable[Any] = ()
) -> List[Dict[str, Any]]:
    cur = conn.execute(query, tuple(params))
    return list(cur.fetchall())


def execute(
    conn: sqlite3.Connection, query: str, params: Iterable[Any] = ()
) -> sqlite3.Cursor:
    return conn.execute(query, tuple(params))
