"""SQLite connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from platformdirs import user_data_dir

_connection: sqlite3.Connection | None = None

SCHEMA = """\
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL DEFAULT 0,
    encoding TEXT NOT NULL DEFAULT 'utf-8',
    word_count INTEGER NOT NULL DEFAULT 0,
    chapter_count INTEGER NOT NULL DEFAULT 0,
    added_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    last_read_at TEXT,
    read_position INTEGER NOT NULL DEFAULT 0,
    read_chapter_idx INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    title TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 2,
    byte_offset INTEGER NOT NULL,
    length INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id, idx);

CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def _db_path() -> Path:
    data_dir = Path(user_data_dir("novel-tui", ensure_exists=True))
    return data_dir / "library.db"


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Get or create singleton SQLite connection."""
    global _connection
    if _connection is not None:
        return _connection

    path = str(db_path) if db_path else str(_db_path())
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _connection = conn
    return conn


def reset_connection() -> None:
    """Close and reset the singleton connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
