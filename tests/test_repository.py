"""Tests for database repository."""

import tempfile
from pathlib import Path

import pytest

from novel_tui.db.connection import get_connection, reset_connection
from novel_tui.db.models import Book, Chapter, UserSettings
from novel_tui.db import repository


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path):
    """Use a fresh temp database for each test."""
    reset_connection()
    db_path = tmp_path / "test.db"
    get_connection(db_path)
    yield
    reset_connection()


def _make_book(**kwargs) -> Book:
    defaults = dict(
        title="Test Book",
        file_path="/tmp/test.txt",
        file_size=1000,
        encoding="utf-8",
        word_count=500,
        chapter_count=5,
    )
    defaults.update(kwargs)
    return Book(**defaults)


def test_add_and_get_book():
    book = _make_book()
    saved = repository.add_book(book)
    assert saved.id is not None

    fetched = repository.get_book(saved.id)
    assert fetched is not None
    assert fetched.title == "Test Book"
    assert fetched.file_path == "/tmp/test.txt"


def test_get_all_books():
    repository.add_book(_make_book(file_path="/tmp/a.txt", title="Book A"))
    repository.add_book(_make_book(file_path="/tmp/b.txt", title="Book B"))

    books = repository.get_all_books()
    assert len(books) == 2


def test_delete_book():
    book = repository.add_book(_make_book())
    repository.delete_book(book.id)

    assert repository.get_book(book.id) is None


def test_update_read_progress():
    book = repository.add_book(_make_book())
    repository.update_read_progress(book.id, chapter_idx=3, position=1500)

    updated = repository.get_book(book.id)
    assert updated.read_chapter_idx == 3
    assert updated.read_position == 1500
    assert updated.last_read_at is not None


def test_add_and_get_chapters():
    book = repository.add_book(_make_book())
    chapters = [
        Chapter(book_id=book.id, index=0, title="Chapter 1", byte_offset=0, length=100),
        Chapter(book_id=book.id, index=1, title="Chapter 2", byte_offset=100, length=200),
    ]
    repository.add_chapters(chapters)

    fetched = repository.get_chapters(book.id)
    assert len(fetched) == 2
    assert fetched[0].title == "Chapter 1"
    assert fetched[1].title == "Chapter 2"


def test_cascade_delete():
    book = repository.add_book(_make_book())
    chapters = [
        Chapter(book_id=book.id, index=0, title="Ch1", byte_offset=0, length=50),
    ]
    repository.add_chapters(chapters)

    repository.delete_book(book.id)
    assert repository.get_chapters(book.id) == []


def test_settings():
    settings = repository.get_settings()
    assert settings.line_spacing == 1
    assert settings.max_width == 80

    new_settings = UserSettings(line_spacing=2, max_width=100)
    repository.save_settings(new_settings)

    loaded = repository.get_settings()
    assert loaded.line_spacing == 2
    assert loaded.max_width == 100
