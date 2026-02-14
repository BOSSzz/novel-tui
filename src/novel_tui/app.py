"""Novel TUI application."""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from novel_tui.db.connection import get_connection


class NovelApp(App):
    """A TUI novel reader application."""

    TITLE = "Novel TUI - 小说阅读器"
    CSS_PATH = [
        Path("styles/colors.tcss"),
        Path("styles/app.tcss"),
        Path("styles/book_list.tcss"),
        Path("styles/reading.tcss"),
    ]

    def on_mount(self) -> None:
        # Initialize database
        get_connection()
        # Push the book list screen
        from novel_tui.screens.book_list import BookListScreen
        self.push_screen(BookListScreen())
