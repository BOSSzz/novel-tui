"""Book list DataTable widget."""

from __future__ import annotations

from textual.widgets import DataTable

from novel_tui.db.models import Book


class BookTable(DataTable):
    """DataTable displaying the book library."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._books: list[Book] = []

    def on_mount(self) -> None:
        self.add_columns("书名", "章节数", "字数", "进度", "添加时间", "上次阅读")

    def load_books(self, books: list[Book]) -> None:
        """Refresh the table with the given book list."""
        self._books = books
        self.clear()
        for book in books:
            word_str = self._format_count(book.word_count)
            progress = self._format_progress(book)
            added = book.added_at.strftime("%Y-%m-%d")
            last_read = book.last_read_at.strftime("%Y-%m-%d %H:%M") if book.last_read_at else "—"
            self.add_row(book.title, str(book.chapter_count), word_str, progress, added, last_read, key=str(book.id))

    def get_selected_book(self) -> Book | None:
        """Get the currently selected book."""
        if not self._books or self.row_count == 0:
            return None
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        key_value = row_key.value if hasattr(row_key, "value") else str(row_key)
        for book in self._books:
            if str(book.id) == key_value:
                return book
        return None

    @staticmethod
    def _format_count(n: int) -> str:
        if n >= 10000:
            return f"{n / 10000:.1f}万"
        return str(n)

    @staticmethod
    def _format_progress(book: Book) -> str:
        if book.chapter_count <= 0:
            return "—"
        idx = book.read_chapter_idx
        total = book.chapter_count
        pct = min((idx + 1) / total * 100, 100)
        if not book.last_read_at:
            return "未读"
        return f"{idx + 1}/{total} ({pct:.0f}%)"
