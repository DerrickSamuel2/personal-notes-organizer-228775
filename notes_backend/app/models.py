"""Pydantic models for the Notes API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base fields shared by create/update operations."""

    title: str = Field(..., description="Note title.")
    content: str = Field(..., description="Note content/body.")
    tags: List[str] = Field(
        default_factory=list, description="List of tag names associated with the note."
    )


class NoteCreate(NoteBase):
    """Request body for creating a note."""


class NoteUpdate(NoteBase):
    """Request body for replacing a note (PUT)."""


class NoteOut(NoteBase):
    """Response model for a note."""

    id: int = Field(..., description="Note ID.")
    created_at: str = Field(..., description="RFC3339 timestamp when the note was created.")
    updated_at: str = Field(..., description="RFC3339 timestamp when the note was last updated.")


class NotesListOut(BaseModel):
    """Response model for listing notes with pagination metadata."""

    items: List[NoteOut] = Field(..., description="Returned notes.")
    total: int = Field(..., description="Total notes matching the query (before pagination).")
    limit: int = Field(..., description="Page size used.")
    offset: int = Field(..., description="Offset used.")


class ErrorOut(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Human-readable error message.")


class TagCountsOut(BaseModel):
    """Optional richer tag response (not currently used by frontend)."""

    name: str = Field(..., description="Tag name.")
    count: int = Field(..., description="Number of notes with this tag.")
