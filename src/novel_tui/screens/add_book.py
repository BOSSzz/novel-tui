"""Add book modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual import work

from novel_tui.core.parser import parse_book
from novel_tui.db import repository
from novel_tui.db.models import Book
from novel_tui.widgets.file_picker import FilePicker


class AddBookModal(ModalScreen[Book | None]):
    """Modal for adding a new book via interactive file picker."""

    BINDINGS = [("escape", "cancel", "取消")]

    def compose(self) -> ComposeResult:
        with Vertical(id="add-book-container"):
            yield Label("添加书籍", id="add-book-title")
            yield FilePicker(id="file-picker")
            yield Label("", id="parse-status")
            with Horizontal(id="btn-row"):
                yield Button("取消", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_file_picker_file_selected(self, event: FilePicker.FileSelected) -> None:
        path = event.path
        if not path.lower().endswith(".txt"):
            self._set_status("仅支持 .txt 文件", error=True)
            return
        self.query_one("#file-picker", FilePicker).disabled = True
        self.query_one("#btn-cancel", Button).disabled = True
        self._set_status("正在解析...")
        self._parse_and_save(path)

    @work(thread=True)
    def _parse_and_save(self, file_path: str) -> None:
        try:
            def on_progress(msg: str) -> None:
                self.app.call_from_thread(self._set_status, msg)

            book, chapters = parse_book(file_path, progress=on_progress)
            self.app.call_from_thread(self._save_to_db, book, chapters)
        except Exception as e:
            self.app.call_from_thread(self._on_parse_error, str(e))

    def _save_to_db(self, book: Book, chapters: list) -> None:
        try:
            self._set_status("保存到数据库...")
            book = repository.add_book(book)
            for ch in chapters:
                ch.book_id = book.id
            repository.add_chapters(chapters)
            self.dismiss(book)
        except Exception as e:
            self._on_parse_error(f"保存失败: {e}")

    def _on_parse_error(self, msg: str) -> None:
        self._set_status(msg, error=True)
        self.query_one("#file-picker", FilePicker).disabled = False
        self.query_one("#btn-cancel", Button).disabled = False
        self.query_one("#file-picker", FilePicker).focus_input()

    def _set_status(self, text: str, error: bool = False) -> None:
        label = self.query_one("#parse-status", Label)
        if error:
            label.update(f"[red]{text}[/red]")
        else:
            label.update(text)
