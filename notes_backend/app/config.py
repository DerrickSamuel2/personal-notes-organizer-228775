"""
Application configuration.

Values are read from environment variables so deployments can configure the service
without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    """Strongly-typed settings for the backend."""

    host: str
    port: int
    cors_origins: List[str]
    sqlite_db_path: str


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load settings from the environment with safe defaults.

    Returns:
        Settings: Application settings object.
    """
    host = os.getenv("HOST", "0.0.0.0")
    port_str = os.getenv("PORT", "3001")

    cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # Default DB location: resolve relative to this backend package directory so it works
    # regardless of the process working directory (e.g., uvicorn started from repo root
    # vs container root).
    default_db_path = (
        Path(__file__).resolve().parents[3]
        / "personal-notes-organizer-228777"
        / "notes_database"
        / "notes.db"
    )
    sqlite_db_path = os.getenv("SQLITE_DB_PATH", str(default_db_path))

    try:
        port = int(port_str)
    except ValueError as exc:
        raise ValueError("PORT must be an integer.") from exc

    return Settings(
        host=host,
        port=port,
        cors_origins=_split_csv(cors_origins_raw),
        sqlite_db_path=sqlite_db_path,
    )
