"""Reading screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Button, Footer, Input, Label
from textual import work

from novel_tui.core.reader import BookReader
from novel_tui.core.search import BookSearcher, SearchResult
from novel_tui.db import repository
from novel_tui.db.models import Book, Chapter, UserSettings
from novel_tui.widgets.chapter_sidebar import ChapterSidebar
from novel_tui.widgets.content_view import ContentView
from novel_tui.widgets.search_bar import SearchBar
from novel_tui.widgets.status_bar import StatusBar


class SettingsModal(ModalScreen[UserSettings | None]):
    """Settings modal for reading preferences."""

    BINDINGS = [("escape", "cancel", "取消")]

    def __init__(self, settings: UserSettings, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._settings = settings

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-container"):
            yield Label("阅读设置")
            yield Label("段落间距 (0/1/2):")
            yield Input(
                value=str(self._settings.line_spacing),
                id="line-spacing-input",
                type="integer",
            )
            yield Label("每行最大字符数:")
            yield Input(
                value=str(self._settings.max_width),
                id="max-width-input",
                type="integer",
            )
            with Horizontal(id="settings-btn-row"):
                yield Button("保存", variant="primary", id="btn-save-settings")
                yield Button("取消", id="btn-cancel-settings")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save-settings":
            try:
                spacing = int(self.query_one("#line-spacing-input", Input).value)
                width = int(self.query_one("#max-width-input", Input).value)
                spacing = max(0, min(2, spacing))
                width = max(40, min(200, width))
                settings = UserSettings(line_spacing=spacing, max_width=width)
                repository.save_settings(settings)
                self.dismiss(settings)
            except ValueError:
                self.notify("请输入有效数字", severity="error")
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ReadingScreen(Screen):
    """Screen for reading a book."""

    BINDINGS = [
        ("escape", "go_back", "返回"),
        ("q", "go_back", "返回"),
        ("left", "prev_chapter", "上一章"),
        ("right", "next_chapter", "下一章"),
        ("t", "toggle_sidebar", "目录"),
        ("slash", "open_search", "搜索"),
        ("n", "next_result", "下一个"),
        ("shift+n", "prev_result", "上一个"),
        ("s", "open_settings", "设置"),
    ]

    def __init__(self, book: Book, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._book_id: int = book.id  # type: ignore[assignment]
        self._book: Book = book
        self._chapters: list[Chapter] = []
        self._current_chapter_idx: int = 0
        self._reader: BookReader | None = None
        self._settings = UserSettings()
        self._search_results: list[SearchResult] = []
        self._search_idx: int = 0
        self._save_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield ChapterSidebar(id="chapter-sidebar")
        with Vertical(id="reading-container"):
            yield ContentView(id="content-view")
            yield SearchBar(id="search-bar")
            yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        # Fetch latest book data from DB to restore saved progress
        fresh = repository.get_book(self._book_id)
        if fresh is not None:
            self._book = fresh

        self._settings = repository.get_settings()
        self._chapters = repository.get_chapters(self._book_id)
        self._reader = BookReader(self._book.file_path, self._book.encoding)

        # Apply format settings
        content = self.query_one("#content-view", ContentView)
        content.set_format(self._settings.max_width, self._settings.line_spacing)

        # Restore saved position — load content first (fast)
        self._current_chapter_idx = self._book.read_chapter_idx
        if self._current_chapter_idx >= len(self._chapters):
            self._current_chapter_idx = 0
        self._load_chapter(self._current_chapter_idx)

        # Build sidebar after first paint so it doesn't block reading
        self.set_timer(0.1, self._deferred_load_sidebar)

        # Auto-save timer (30 seconds)
        self._save_timer = self.set_interval(30, self._save_progress)

    def _deferred_load_sidebar(self) -> None:
        sidebar = self.query_one("#chapter-sidebar", ChapterSidebar)
        sidebar.load_chapters(self._chapters, self._current_chapter_idx)

    def on_unmount(self) -> None:
        self._save_progress()
        if self._save_timer:
            self._save_timer.stop()

    def _load_chapter(self, idx: int) -> None:
        """Load and display a chapter."""
        if not self._chapters or not self._reader:
            return
        if idx < 0 or idx >= len(self._chapters):
            return

        self._current_chapter_idx = idx
        chapter = self._chapters[idx]

        try:
            text = self._reader.read_chapter(chapter)
        except FileNotFoundError:
            self.notify("文件不存在，可能已被移动或删除", severity="error")
            return

        content = self.query_one("#content-view", ContentView)
        content.set_content(text)
        content.scroll_home(animate=False)
        content.focus()

        # Update status bar
        status = self.query_one("#status-bar", StatusBar)
        status.update_status(chapter.title, idx, len(self._chapters))

        # Update sidebar
        sidebar = self.query_one("#chapter-sidebar", ChapterSidebar)
        sidebar.highlight_chapter(idx)

    def _save_progress(self) -> None:
        """Save current reading position."""
        repository.update_read_progress(
            self._book_id,
            self._current_chapter_idx,
            0,
        )

    def action_go_back(self) -> None:
        search_bar = self.query_one("#search-bar", SearchBar)
        if search_bar.is_visible:
            search_bar.hide()
            content = self.query_one("#content-view", ContentView)
            content.clear_search_highlight()
            self._search_results = []
            return
        self._save_progress()
        self.app.pop_screen()

    def action_prev_chapter(self) -> None:
        if self._current_chapter_idx > 0:
            self._load_chapter(self._current_chapter_idx - 1)

    def action_next_chapter(self) -> None:
        if self._current_chapter_idx < len(self._chapters) - 1:
            self._load_chapter(self._current_chapter_idx + 1)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#chapter-sidebar", ChapterSidebar)
        sidebar.toggle()

    def action_open_search(self) -> None:
        search_bar = self.query_one("#search-bar", SearchBar)
        search_bar.show()

    def action_open_settings(self) -> None:
        def on_settings(result: UserSettings | None) -> None:
            if result is not None:
                self._settings = result
                content = self.query_one("#content-view", ContentView)
                content.set_format(result.max_width, result.line_spacing)

        self.app.push_screen(SettingsModal(self._settings), callback=on_settings)

    def action_next_result(self) -> None:
        if not self._search_results:
            return
        self._search_idx = (self._search_idx + 1) % len(self._search_results)
        self._navigate_to_result()

    def action_prev_result(self) -> None:
        if not self._search_results:
            return
        self._search_idx = (self._search_idx - 1) % len(self._search_results)
        self._navigate_to_result()

    def _navigate_to_result(self) -> None:
        """Navigate to the current search result."""
        if not self._search_results:
            return
        result = self._search_results[self._search_idx]
        if result.chapter_idx != self._current_chapter_idx:
            self._load_chapter(result.chapter_idx)

        # Scroll to the matching position within the chapter
        content = self.query_one("#content-view", ContentView)
        content.scroll_to_char_offset(result.char_offset)

        search_bar = self.query_one("#search-bar", SearchBar)
        search_bar.update_results(len(self._search_results), self._search_idx + 1)

    def on_chapter_sidebar_chapter_selected(self, event: ChapterSidebar.ChapterSelected) -> None:
        self._load_chapter(event.chapter_idx)
        # Auto-hide sidebar after selection
        sidebar = self.query_one("#chapter-sidebar", ChapterSidebar)
        sidebar.toggle()

    def on_search_bar_search_requested(self, event: SearchBar.SearchRequested) -> None:
        self._do_search(event.query)

    def on_search_bar_search_closed(self, event: SearchBar.SearchClosed) -> None:
        content = self.query_one("#content-view", ContentView)
        content.clear_search_highlight()
        self._search_results = []
        self._search_idx = 0

    @work(thread=True)
    def _do_search(self, query: str) -> None:
        """Perform full-text search in background."""
        if not self._reader:
            return
        searcher = BookSearcher(self._reader, self._chapters)
        results = searcher.search(query)
        self.app.call_from_thread(self._on_search_done, query, results)

    def _on_search_done(self, query: str, results: list[SearchResult]) -> None:
        """Handle search results."""
        self._search_results = results
        self._search_idx = 0

        search_bar = self.query_one("#search-bar", SearchBar)
        content = self.query_one("#content-view", ContentView)

        if results:
            search_bar.update_results(len(results), 1)
            content.set_search_highlight(query)
            # Navigate to first result in or after current chapter
            for i, r in enumerate(results):
                if r.chapter_idx >= self._current_chapter_idx:
                    self._search_idx = i
                    break
            self._navigate_to_result()
        else:
            search_bar.update_results(0, 0)
            content.clear_search_highlight()

        # Move focus back to content so n/N keys work
        content.focus()
