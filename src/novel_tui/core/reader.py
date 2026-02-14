"""File reader with offset-based seeking."""

from __future__ import annotations

from pathlib import Path

from novel_tui.db.models import Chapter


class BookReader:
    """Reads chapter content from a book file using byte offsets."""

    def __init__(self, file_path: str | Path, encoding: str = "utf-8") -> None:
        self.file_path = Path(file_path)
        self.encoding = encoding

    def read_chapter(self, chapter: Chapter) -> str:
        """Read a single chapter's content by its byte offset and length."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        with open(self.file_path, "rb") as f:
            f.seek(chapter.byte_offset)
            raw = f.read(chapter.length)
        return raw.decode(self.encoding, errors="replace")

    def read_range(self, offset: int, length: int) -> str:
        """Read arbitrary byte range."""
        with open(self.file_path, "rb") as f:
            f.seek(offset)
            raw = f.read(length)
        return raw.decode(self.encoding, errors="replace")
