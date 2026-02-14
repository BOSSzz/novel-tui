"""Vim-style search bar widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label


class SearchBar(Widget):
    """Inline search bar with result navigation."""

    class SearchRequested(Message):
        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    class SearchClosed(Message):
        pass

    class NavigateResult(Message):
        def __init__(self, direction: int) -> None:
            super().__init__()
            self.direction = direction  # 1 = next, -1 = previous

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._result_count: int = 0
        self._current_result: int = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(placeholder="搜索...", id="search-input")
            yield Label("", id="search-count")

    def show(self) -> None:
        """Show the search bar and focus input."""
        self.add_class("visible")
        self.query_one("#search-input", Input).focus()

    def hide(self) -> None:
        """Hide the search bar."""
        self.remove_class("visible")
        self.query_one("#search-input", Input).value = ""
        self._update_count_label()
        self.post_message(self.SearchClosed())

    def update_results(self, total: int, current: int) -> None:
        """Update the result count display."""
        self._result_count = total
        self._current_result = current
        self._update_count_label()

    def _update_count_label(self) -> None:
        label = self.query_one("#search-count", Label)
        if self._result_count > 0:
            label.update(f"{self._current_result}/{self._result_count}")
        elif self.has_class("visible") and self.query_one("#search-input", Input).value:
            label.update("无结果")
        else:
            label.update("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input" and event.value.strip():
            self.post_message(self.SearchRequested(event.value.strip()))

    @property
    def is_visible(self) -> bool:
        return self.has_class("visible")
