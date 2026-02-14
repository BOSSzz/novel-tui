"""Book list (shelf) screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Label

from novel_tui.db import repository
from novel_tui.db.models import Book
from novel_tui.screens.add_book import AddBookModal
from novel_tui.widgets.book_table import BookTable


class ConfirmDeleteModal(ModalScreen[bool]):
    """Confirmation dialog for deleting a book."""

    BINDINGS = [("escape", "cancel", "取消")]

    def __init__(self, book_title: str, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._book_title = book_title

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-container"):
            yield Label(f"确定要删除《{self._book_title}》吗？")
            yield Label("此操作不可撤销")
            with Horizontal(id="confirm-btn-row"):
                yield Button("删除", variant="error", id="btn-delete")
                yield Button("取消", id="btn-cancel-del")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-delete")

    def action_cancel(self) -> None:
        self.dismiss(False)


class BookListScreen(Screen):
    """Main book shelf screen."""

    BINDINGS = [
        ("a", "add_book", "添加书籍"),
        ("d", "delete_book", "删除书籍"),
        ("q", "quit", "退出"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield BookTable(id="book-table")
        yield Label("书架为空，按 [bold]a[/bold] 添加书籍", id="empty-label")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_books()

    def on_screen_resume(self) -> None:
        self._refresh_books()

    def _refresh_books(self) -> None:
        books = repository.get_all_books()
        table = self.query_one("#book-table", BookTable)
        empty_label = self.query_one("#empty-label", Label)
        table.load_books(books)
        if books:
            table.display = True
            empty_label.display = False
        else:
            table.display = False
            empty_label.display = True

    def action_add_book(self) -> None:
        def on_dismiss(result: Book | None) -> None:
            if result is not None:
                self.notify(f"已添加《{result.title}》({result.chapter_count} 章)")
                self._refresh_books()

        self.app.push_screen(AddBookModal(), callback=on_dismiss)

    def action_delete_book(self) -> None:
        table = self.query_one("#book-table", BookTable)
        book = table.get_selected_book()
        if book is None:
            self.notify("没有选中的书籍", severity="warning")
            return

        def on_confirm(confirmed: bool) -> None:
            if confirmed and book.id is not None:
                repository.delete_book(book.id)
                self.notify(f"已删除《{book.title}》")
                self._refresh_books()

        self.app.push_screen(ConfirmDeleteModal(book.title), callback=on_confirm)

    def action_open_book(self) -> None:
        table = self.query_one("#book-table", BookTable)
        book = table.get_selected_book()
        if book is None:
            self.notify("未找到选中书籍", severity="warning")
            return
        from novel_tui.screens.reading import ReadingScreen
        self.app.push_screen(ReadingScreen(book))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_open_book()

    def action_quit(self) -> None:
        self.app.exit()
