"""Chapter sidebar widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, ListView, ListItem

from novel_tui.db.models import Chapter


class ChapterSidebar(Widget):
    """Sidebar showing chapter table of contents."""

    class ChapterSelected(Message):
        """Posted when a chapter is selected."""

        def __init__(self, chapter_idx: int) -> None:
            super().__init__()
            self.chapter_idx = chapter_idx

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._chapters: list[Chapter] = []
        self._current_idx: int = 0
        self._items: list[ListItem] = []

    def compose(self) -> ComposeResult:
        yield Label("目录", id="sidebar-title")
        yield ListView(id="chapter-list")

    def load_chapters(self, chapters: list[Chapter], current_idx: int = 0) -> None:
        """Build the list once. Only called on screen mount."""
        self._chapters = chapters
        self._current_idx = current_idx
        list_view = self.query_one("#chapter-list", ListView)
        list_view.clear()
        self._items = []
        for ch in chapters:
            prefix = "  " if ch.level == 2 else ""
            marker = "▶ " if ch.index == current_idx else "  "
            label_text = f"{marker}{prefix}{ch.title}"
            item = ListItem(Label(label_text), name=str(ch.index))
            if ch.level == 1:
                item.add_class("level-1")
            else:
                item.add_class("level-2")
            if ch.index == current_idx:
                item.add_class("current")
            self._items.append(item)
            list_view.append(item)

    def highlight_chapter(self, idx: int) -> None:
        """Update highlight by toggling CSS classes — no rebuild."""
        if not self._items:
            return
        # Remove highlight from old item
        if 0 <= self._current_idx < len(self._items):
            old = self._items[self._current_idx]
            old.remove_class("current")
            old.query_one(Label).update(self._make_label(self._current_idx, current=False))
        # Add highlight to new item
        self._current_idx = idx
        if 0 <= idx < len(self._items):
            new = self._items[idx]
            new.add_class("current")
            new.query_one(Label).update(self._make_label(idx, current=True))

    def _make_label(self, idx: int, *, current: bool) -> str:
        ch = self._chapters[idx]
        prefix = "  " if ch.level == 2 else ""
        marker = "▶ " if current else "  "
        return f"{marker}{prefix}{ch.title}"

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.name is not None:
            self.post_message(self.ChapterSelected(int(event.item.name)))

    def toggle(self) -> None:
        self.toggle_class("visible")
