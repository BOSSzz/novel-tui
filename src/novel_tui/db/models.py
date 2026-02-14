"""Data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Book:
    title: str
    file_path: str
    file_size: int = 0
    encoding: str = "utf-8"
    word_count: int = 0
    chapter_count: int = 0
    added_at: datetime = field(default_factory=datetime.now)
    last_read_at: datetime | None = None
    read_position: int = 0
    read_chapter_idx: int = 0
    id: int | None = None


@dataclass
class Chapter:
    book_id: int
    index: int
    title: str
    byte_offset: int
    length: int = 0
    level: int = 2
    id: int | None = None


@dataclass
class UserSettings:
    line_spacing: int = 1
    max_width: int = 80
