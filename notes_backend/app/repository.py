"""
Repository layer implementing CRUD and search/filtering.

Schema is defined by notes_database/init_db.py:
- notes(id, title, content, created_at, updated_at)
- tags(id, name, created_at)
- note_tags(note_id, tag_id, created_at)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import sqlite3

from .db import execute, fetch_all, fetch_one


def _normalize_tag(tag: str) -> str:
    return tag.strip()


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _get_or_create_tag_ids(conn: sqlite3.Connection, tags: Sequence[str]) -> List[int]:
    normalized = [_normalize_tag(t) for t in tags if _normalize_tag(t)]
    normalized = _dedupe_preserve_order(normalized)
    if not normalized:
        return []

    tag_ids: List[int] = []
    for name in normalized:
        row = fetch_one(conn, "SELECT id FROM tags WHERE name = ?;", (name,))
        if row is None:
            cur = execute(conn, "INSERT INTO tags(name) VALUES (?);", (name,))
            tag_ids.append(int(cur.lastrowid))
        else:
            tag_ids.append(int(row["id"]))
    return tag_ids


def _replace_note_tags(
    conn: sqlite3.Connection, note_id: int, tags: Sequence[str]
) -> List[str]:
    """Replace tags for a note and return the normalized tag names."""
    normalized = [_normalize_tag(t) for t in tags if _normalize_tag(t)]
    normalized = _dedupe_preserve_order(normalized)

    # Remove all existing mappings then insert new ones.
    execute(conn, "DELETE FROM note_tags WHERE note_id = ?;", (note_id,))
    tag_ids = _get_or_create_tag_ids(conn, normalized)

    for tag_id in tag_ids:
        execute(
            conn,
            "INSERT OR IGNORE INTO note_tags(note_id, tag_id) VALUES (?, ?);",
            (note_id, tag_id),
        )

    return normalized


def _note_tags(conn: sqlite3.Connection, note_id: int) -> List[str]:
    rows = fetch_all(
        conn,
        """
        SELECT t.name AS name
        FROM tags t
        INNER JOIN note_tags nt ON nt.tag_id = t.id
        WHERE nt.note_id = ?
        ORDER BY t.name ASC;
        """,
        (note_id,),
    )
    return [str(r["name"]) for r in rows]


def _note_out(conn: sqlite3.Connection, note_row: Dict[str, Any]) -> Dict[str, Any]:
    note_id = int(note_row["id"])
    return {
        "id": note_id,
        "title": str(note_row["title"]),
        "content": str(note_row["content"]),
        "created_at": str(note_row["created_at"]),
        "updated_at": str(note_row["updated_at"]),
        "tags": _note_tags(conn, note_id),
    }


# PUBLIC_INTERFACE
def list_notes(
    conn: sqlite3.Connection,
    q: Optional[str],
    tag: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[Dict[str, Any]], int]:
    """List notes with optional full-text-like search and tag filtering.

    Search behavior:
      - If q is provided, matches title/content with LIKE (case-insensitive for ASCII).
    Tag filter:
      - If tag is provided, returns notes linked to that tag name.

    Returns:
        (items, total)
    """
    where: List[str] = []
    params: List[Any] = []

    join = ""
    if tag and tag.strip():
        join = """
        INNER JOIN note_tags nt ON nt.note_id = n.id
        INNER JOIN tags t ON t.id = nt.tag_id
        """
        where.append("t.name = ?")
        params.append(tag.strip())

    if q and q.strip():
        where.append("(n.title LIKE ? ESCAPE '\\' OR n.content LIKE ? ESCAPE '\\')")
        like = f"%{q.strip()}%"
        params.extend([like, like])

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    total_row = fetch_one(
        conn,
        f"""
        SELECT COUNT(DISTINCT n.id) AS cnt
        FROM notes n
        {join}
        {where_sql};
        """,
        params,
    )
    total = int(total_row["cnt"]) if total_row else 0

    rows = fetch_all(
        conn,
        f"""
        SELECT DISTINCT n.*
        FROM notes n
        {join}
        {where_sql}
        ORDER BY n.updated_at DESC
        LIMIT ? OFFSET ?;
        """,
        params + [limit, offset],
    )

    items = [_note_out(conn, r) for r in rows]
    return items, total


# PUBLIC_INTERFACE
def get_note(conn: sqlite3.Connection, note_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single note by ID (including tags)."""
    row = fetch_one(conn, "SELECT * FROM notes WHERE id = ?;", (note_id,))
    if row is None:
        return None
    return _note_out(conn, row)


# PUBLIC_INTERFACE
def create_note(
    conn: sqlite3.Connection, title: str, content: str, tags: Sequence[str]
) -> Dict[str, Any]:
    """Create a note and return it."""
    cur = execute(
        conn,
        "INSERT INTO notes(title, content) VALUES (?, ?);",
        (title, content),
    )
    note_id = int(cur.lastrowid)
    _replace_note_tags(conn, note_id, tags)

    row = fetch_one(conn, "SELECT * FROM notes WHERE id = ?;", (note_id,))
    # Should never be None immediately after insert.
    assert row is not None
    return _note_out(conn, row)


# PUBLIC_INTERFACE
def update_note(
    conn: sqlite3.Connection,
    note_id: int,
    title: str,
    content: str,
    tags: Sequence[str],
) -> Optional[Dict[str, Any]]:
    """Replace note fields (PUT semantics). Returns updated note or None if missing."""
    existing = fetch_one(conn, "SELECT id FROM notes WHERE id = ?;", (note_id,))
    if existing is None:
        return None

    execute(
        conn,
        "UPDATE notes SET title = ?, content = ? WHERE id = ?;",
        (title, content, note_id),
    )
    _replace_note_tags(conn, note_id, tags)

    row = fetch_one(conn, "SELECT * FROM notes WHERE id = ?;", (note_id,))
    assert row is not None
    return _note_out(conn, row)


# PUBLIC_INTERFACE
def delete_note(conn: sqlite3.Connection, note_id: int) -> bool:
    """Delete a note. Returns True if it existed and was deleted."""
    cur = execute(conn, "DELETE FROM notes WHERE id = ?;", (note_id,))
    return cur.rowcount > 0


# PUBLIC_INTERFACE
def list_tags(conn: sqlite3.Connection) -> List[str]:
    """List all tags as simple array of strings (what frontend expects)."""
    rows = fetch_all(conn, "SELECT name FROM tags ORDER BY name ASC;")
    return [str(r["name"]) for r in rows]
