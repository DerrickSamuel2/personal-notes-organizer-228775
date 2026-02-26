"""
FastAPI backend for the Personal Notes Organizer.

Provides REST endpoints for CRUD operations on notes and tags, backed by SQLite.

Frontend expectation:
- The Next.js frontend reads NEXT_PUBLIC_API_BASE and calls:
  - GET    /healthz
  - GET    /notes
  - POST   /notes
  - PUT    /notes/{id}
  - DELETE /notes/{id}
  - GET    /tags
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import get_conn
from .models import ErrorOut, NoteCreate, NoteOut, NotesListOut, NoteUpdate
from .repository import (
    create_note as repo_create_note,
    delete_note as repo_delete_note,
    get_note as repo_get_note,
    list_notes as repo_list_notes,
    list_tags as repo_list_tags,
    update_note as repo_update_note,
)

settings = get_settings()

openapi_tags = [
    {"name": "Health", "description": "Service liveness/readiness checks."},
    {"name": "Notes", "description": "Create, list, update, delete notes and search/filter them."},
    {"name": "Tags", "description": "List available tags."},
]

app = FastAPI(
    title="Personal Notes Organizer API",
    description="REST API for local personal notes with optional tags (single-user, no auth).",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# CORS for browser-based Next.js frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get(
    "/healthz",
    tags=["Health"],
    summary="Health check",
    response_model=dict,
    operation_id="healthz",
)
def healthz() -> dict:
    """Health check endpoint.

    Returns:
        dict: `{"ok": true}`
    """
    return {"ok": True}


# PUBLIC_INTERFACE
@app.get(
    "/notes",
    tags=["Notes"],
    summary="List notes",
    response_model=list[NoteOut],
    operation_id="listNotes",
    responses={400: {"model": ErrorOut}},
)
def list_notes(
    q: Optional[str] = Query(
        default=None, description="Search query applied to title/content (LIKE)."
    ),
    tag: Optional[str] = Query(
        default=None, description="Filter by a specific tag name."
    ),
    limit: int = Query(default=200, ge=1, le=500, description="Maximum notes to return."),
    offset: int = Query(default=0, ge=0, description="Offset for pagination."),
) -> list[NoteOut]:
    """List notes with optional search and tag filter.

    Note: frontend currently expects a raw array (not paginated envelope), so this endpoint
    returns just the items.
    """
    with get_conn(settings.sqlite_db_path) as conn:
        items, _total = repo_list_notes(conn, q=q, tag=tag, limit=limit, offset=offset)
        return items  # type: ignore[return-value]


# PUBLIC_INTERFACE
@app.post(
    "/notes",
    tags=["Notes"],
    summary="Create note",
    response_model=NoteOut,
    operation_id="createNote",
    responses={400: {"model": ErrorOut}},
)
def create_note(payload: NoteCreate) -> NoteOut:
    """Create a new note.

    Body:
      - title: string
      - content: string
      - tags: string[] (optional)
    """
    with get_conn(settings.sqlite_db_path) as conn:
        with conn:
            created = repo_create_note(
                conn, title=payload.title, content=payload.content, tags=payload.tags
            )
        return created  # type: ignore[return-value]


# PUBLIC_INTERFACE
@app.get(
    "/notes/{note_id}",
    tags=["Notes"],
    summary="Get note",
    response_model=NoteOut,
    operation_id="getNote",
    responses={404: {"model": ErrorOut}},
)
def get_note(note_id: int) -> NoteOut:
    """Get a single note by ID."""
    with get_conn(settings.sqlite_db_path) as conn:
        note = repo_get_note(conn, note_id=note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found.")
        return note  # type: ignore[return-value]


# PUBLIC_INTERFACE
@app.put(
    "/notes/{note_id}",
    tags=["Notes"],
    summary="Update note",
    response_model=NoteOut,
    operation_id="updateNote",
    responses={404: {"model": ErrorOut}},
)
def update_note(note_id: int, payload: NoteUpdate) -> NoteOut:
    """Replace a note (PUT).

    Body:
      - title: string
      - content: string
      - tags: string[] (optional)
    """
    with get_conn(settings.sqlite_db_path) as conn:
        with conn:
            updated = repo_update_note(
                conn,
                note_id=note_id,
                title=payload.title,
                content=payload.content,
                tags=payload.tags,
            )
        if updated is None:
            raise HTTPException(status_code=404, detail="Note not found.")
        return updated  # type: ignore[return-value]


# PUBLIC_INTERFACE
@app.delete(
    "/notes/{note_id}",
    tags=["Notes"],
    summary="Delete note",
    operation_id="deleteNote",
    status_code=204,
    responses={404: {"model": ErrorOut}},
)
def delete_note(note_id: int) -> Response:
    """Delete a note."""
    with get_conn(settings.sqlite_db_path) as conn:
        with conn:
            ok = repo_delete_note(conn, note_id=note_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Note not found.")
        return Response(status_code=204)


# PUBLIC_INTERFACE
@app.get(
    "/tags",
    tags=["Tags"],
    summary="List tags",
    response_model=list[str],
    operation_id="listTags",
)
def list_tags() -> list[str]:
    """List all tags as an array of strings (tag names)."""
    with get_conn(settings.sqlite_db_path) as conn:
        return repo_list_tags(conn)
