"""Reading progress status bar."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    """Status bar showing reading progress."""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("", id="status-chapter")
            yield Label("", id="status-progress")

    def update_status(
        self,
        chapter_title: str,
        chapter_idx: int,
        total_chapters: int,
    ) -> None:
        """Update the status bar information."""
        self.query_one("#status-chapter", Label).update(
            f" {chapter_title}"
        )
        percent = ((chapter_idx + 1) / total_chapters * 100) if total_chapters > 0 else 0
        self.query_one("#status-progress", Label).update(
            f"[{chapter_idx + 1}/{total_chapters}] {percent:.1f}% "
        )
