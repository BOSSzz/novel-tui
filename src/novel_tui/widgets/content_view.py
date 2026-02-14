"""Reading content display widget with logical-line scrolling."""

from __future__ import annotations

import textwrap

from rich.text import Text
from textual.events import MouseScrollDown, MouseScrollUp
from textual.widget import Widget

# Left/right padding (characters)
_PAD = 4
_PAD_STR = " " * _PAD


class ContentView(Widget, can_focus=True):
    """Custom viewer: scrolls by logical line, wraps by column width."""

    BINDINGS = [
        ("up", "scroll_up_line", "上滚"),
        ("down", "scroll_down_line", "下滚"),
        ("pageup", "page_up", "上翻页"),
        ("pagedown", "page_down", "下翻页"),
        ("home", "scroll_home_action", "顶部"),
        ("end", "scroll_end", "底部"),
    ]

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._max_width: int = 80
        self._line_spacing: int = 1
        self._lines: list[str] = []  # logical lines (paragraphs)
        self._line_char_offsets: list[int] = []  # char offset per logical line
        self._top_line: int = 0
        self._highlight_query: str = ""

    # ── public API ──

    def set_content(self, text: str) -> None:
        paragraphs = text.split("\n")
        self._lines = []
        self._line_char_offsets = []
        pos = 0
        for p in paragraphs:
            stripped = p.strip()
            if stripped:
                self._lines.append(stripped)
                self._line_char_offsets.append(pos)
            pos += len(p) + 1  # +1 for \n
        self._top_line = 0
        self.refresh()

    def set_format(self, max_width: int, line_spacing: int) -> None:
        self._max_width = max_width
        self._line_spacing = line_spacing
        self.refresh()

    def scroll_home(self, animate: bool = False) -> None:
        self._top_line = 0
        self.refresh()

    def set_search_highlight(self, query: str) -> None:
        self._highlight_query = query
        self.refresh()

    def clear_search_highlight(self) -> None:
        self._highlight_query = ""
        self.refresh()

    def scroll_to_char_offset(self, char_offset: int) -> None:
        """Scroll so that the logical line containing char_offset is visible."""
        target_line = 0
        for i, off in enumerate(self._line_char_offsets):
            if off <= char_offset:
                target_line = i
            else:
                break
        self._top_line = target_line
        self.refresh()

    # ── internal ──

    def _wrap_width(self) -> int:
        avail = self.size.width - _PAD * 2
        if avail <= 0:
            avail = 80
        return min(self._max_width, avail) if self._max_width > 0 else avail

    def _wrap_line(self, line: str, width: int) -> list[str]:
        return textwrap.wrap(line, width=width) or [""]

    # ── rendering ──

    def render(self) -> Text:
        if not self._lines:
            return Text("")

        height = self.size.height
        width = self._wrap_width()

        rows: list[str] = []
        line_idx = self._top_line

        while len(rows) < height and line_idx < len(self._lines):
            wrapped = self._wrap_line(self._lines[line_idx], width)
            for vl in wrapped:
                rows.append(_PAD_STR + vl)
            # spacing between logical lines
            if line_idx < len(self._lines) - 1:
                for _ in range(self._line_spacing):
                    rows.append("")
            line_idx += 1

        rows = rows[:height]
        while len(rows) < height:
            rows.append("")

        result = Text("\n".join(rows))
        if self._highlight_query:
            result.highlight_words(
                [self._highlight_query], style="black on yellow", case_sensitive=False
            )
        return result

    # ── scrolling ──

    def _visible_line_count(self) -> int:
        """How many logical lines fit on the current page."""
        height = self.size.height
        width = self._wrap_width()
        visual = 0
        count = 0
        idx = self._top_line
        while idx < len(self._lines):
            h = len(self._wrap_line(self._lines[idx], width))
            space = self._line_spacing if idx < len(self._lines) - 1 else 0
            if visual + h + space > height and count > 0:
                break
            visual += h + space
            count += 1
            idx += 1
        return max(count, 1)

    def action_scroll_down_line(self) -> None:
        if self._top_line < len(self._lines) - 1:
            self._top_line += 1
            self.refresh()

    def action_scroll_up_line(self) -> None:
        if self._top_line > 0:
            self._top_line -= 1
            self.refresh()

    def action_page_down(self) -> None:
        page = self._visible_line_count()
        new_top = min(self._top_line + page, len(self._lines) - 1)
        if new_top != self._top_line:
            self._top_line = new_top
            self.refresh()

    def action_page_up(self) -> None:
        height = self.size.height
        width = self._wrap_width()
        visual = 0
        idx = self._top_line - 1
        while idx >= 0:
            h = len(self._wrap_line(self._lines[idx], width))
            space = self._line_spacing
            if visual + h + space > height:
                idx += 1
                break
            visual += h + space
            idx -= 1
        self._top_line = max(0, idx)
        self.refresh()

    def action_scroll_home_action(self) -> None:
        self._top_line = 0
        self.refresh()

    def action_scroll_end(self) -> None:
        height = self.size.height
        width = self._wrap_width()
        visual = 0
        idx = len(self._lines) - 1
        while idx >= 0:
            h = len(self._wrap_line(self._lines[idx], width))
            space = self._line_spacing if idx < len(self._lines) - 1 else 0
            if visual + h + space > height:
                idx += 1
                break
            visual += h + space
            idx -= 1
        self._top_line = max(0, idx)
        self.refresh()

    # ── mouse wheel ──

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:
        self.action_scroll_down_line()
        event.stop()

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:
        self.action_scroll_up_line()
        event.stop()
