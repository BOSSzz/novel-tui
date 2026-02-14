"""Data access layer."""

from __future__ import annotations

from datetime import datetime

from novel_tui.db.connection import get_connection
from novel_tui.db.models import Book, Chapter, UserSettings


# ── Book CRUD ──


def add_book(book: Book) -> Book:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO books (title, file_path, file_size, encoding, word_count,
           chapter_count, added_at, last_read_at, read_position, read_chapter_idx)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            book.title,
            book.file_path,
            book.file_size,
            book.encoding,
            book.word_count,
            book.chapter_count,
            book.added_at.strftime("%Y-%m-%d %H:%M:%S"),
            book.last_read_at.strftime("%Y-%m-%d %H:%M:%S") if book.last_read_at else None,
            book.read_position,
            book.read_chapter_idx,
        ),
    )
    conn.commit()
    book.id = cur.lastrowid
    return book


def get_all_books() -> list[Book]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM books ORDER BY last_read_at DESC NULLS LAST, added_at DESC").fetchall()
    return [_row_to_book(r) for r in rows]


def get_book(book_id: int) -> Book | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    return _row_to_book(row) if row else None


def delete_book(book_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()


def update_read_progress(book_id: int, chapter_idx: int, position: int) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE books SET read_chapter_idx = ?, read_position = ?,
           last_read_at = datetime('now','localtime') WHERE id = ?""",
        (chapter_idx, position, book_id),
    )
    conn.commit()


def _row_to_book(row: object) -> Book:
    return Book(
        id=row["id"],
        title=row["title"],
        file_path=row["file_path"],
        file_size=row["file_size"],
        encoding=row["encoding"],
        word_count=row["word_count"],
        chapter_count=row["chapter_count"],
        added_at=datetime.strptime(row["added_at"], "%Y-%m-%d %H:%M:%S"),
        last_read_at=(
            datetime.strptime(row["last_read_at"], "%Y-%m-%d %H:%M:%S")
            if row["last_read_at"]
            else None
        ),
        read_position=row["read_position"],
        read_chapter_idx=row["read_chapter_idx"],
    )


# ── Chapter CRUD ──


def add_chapters(chapters: list[Chapter]) -> None:
    conn = get_connection()
    conn.executemany(
        """INSERT INTO chapters (book_id, idx, title, level, byte_offset, length)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(c.book_id, c.index, c.title, c.level, c.byte_offset, c.length) for c in chapters],
    )
    conn.commit()


def get_chapters(book_id: int) -> list[Chapter]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chapters WHERE book_id = ? ORDER BY idx", (book_id,)
    ).fetchall()
    return [
        Chapter(
            id=r["id"],
            book_id=r["book_id"],
            index=r["idx"],
            title=r["title"],
            level=r["level"],
            byte_offset=r["byte_offset"],
            length=r["length"],
        )
        for r in rows
    ]


# ── Settings ──


def get_settings() -> UserSettings:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    data = {r["key"]: r["value"] for r in rows}
    return UserSettings(
        line_spacing=int(data.get("line_spacing", "1")),
        max_width=int(data.get("max_width", "80")),
    )


def save_settings(settings: UserSettings) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('line_spacing', ?)",
        (str(settings.line_spacing),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('max_width', ?)",
        (str(settings.max_width),),
    )
    conn.commit()
