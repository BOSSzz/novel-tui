"""Interactive file picker widget with autocomplete."""

from __future__ import annotations

import os
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.events import Key
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label

_MAX_VISIBLE = 15


class FilePicker(Widget):
    """File path picker with directory browsing and autocomplete.

    Type to filter, Up/Down to select, Tab to fill, Enter to confirm.
    """

    class FileSelected(Message):
        """Posted when user confirms a .txt file."""

        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._entries: list[tuple[Path, bool]] = []  # (path, is_dir)
        self._selected_idx: int = 0
        self._labels: list[Label] = []

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="输入路径, ↑↓ 选择, Tab 填充, Enter 确认",
            id="fp-input",
        )
        with VerticalScroll(id="fp-list"):
            for i in range(_MAX_VISIBLE):
                yield Label("", id=f"fp-{i}", classes="fp-entry")

    def on_mount(self) -> None:
        self._labels = [
            self.query_one(f"#fp-{i}", Label) for i in range(_MAX_VISIBLE)
        ]
        inp = self.query_one("#fp-input", Input)
        home = str(Path.home()) + "/"
        inp.value = home
        inp.cursor_position = len(home)
        inp.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "fp-input":
            self._selected_idx = 0
            self._scan()

    def on_key(self, event: Key) -> None:
        if event.key == "down" and self._entries:
            self._selected_idx = min(
                self._selected_idx + 1, len(self._entries) - 1
            )
            self._render_list()
            event.prevent_default()
            event.stop()
        elif event.key == "up" and self._entries:
            self._selected_idx = max(self._selected_idx - 1, 0)
            self._render_list()
            event.prevent_default()
            event.stop()
        elif event.key == "tab":
            self._fill_selected()
            event.prevent_default()
            event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "fp-input":
            return
        event.stop()
        self._confirm()

    def focus_input(self) -> None:
        """Focus the input field."""
        self.query_one("#fp-input", Input).focus()

    # ── internal ──

    def _parse_input(self) -> tuple[Path | None, str]:
        """Split current input into (existing_directory, name_prefix)."""
        text = self.query_one("#fp-input", Input).value.strip()
        if not text:
            return Path.home(), ""
        p = Path(text).expanduser()
        if text.endswith(("/", "\\")):
            return p if p.is_dir() else None, ""
        return p.parent if p.parent.is_dir() else None, p.name

    def _scan(self) -> None:
        """Read directory and filter entries matching the typed prefix."""
        dir_path, prefix = self._parse_input()
        entries: list[tuple[Path, bool]] = []
        if dir_path is not None:
            try:
                for de in os.scandir(dir_path):
                    if de.name.startswith("."):
                        continue
                    is_dir = de.is_dir(follow_symlinks=True)
                    if prefix and not de.name.lower().startswith(prefix.lower()):
                        continue
                    if is_dir or de.name.lower().endswith(".txt"):
                        entries.append((Path(de.path), is_dir))
            except (PermissionError, OSError):
                pass
        # Directories first, then files; alphabetical within each group
        entries.sort(key=lambda e: (not e[1], e[0].name.lower()))
        self._entries = entries[:_MAX_VISIBLE]
        self._selected_idx = min(
            self._selected_idx, max(0, len(self._entries) - 1)
        )
        self._render_list()

    def _render_list(self) -> None:
        for i, label in enumerate(self._labels):
            if i < len(self._entries):
                path, is_dir = self._entries[i]
                suffix = "/" if is_dir else ""
                label.update(f" {path.name}{suffix}")
                label.display = True
                if is_dir:
                    label.add_class("fp-dir")
                else:
                    label.remove_class("fp-dir")
                if i == self._selected_idx:
                    label.add_class("fp-selected")
                else:
                    label.remove_class("fp-selected")
            else:
                label.display = False
                label.remove_class("fp-selected", "fp-dir")
        # Scroll the highlighted entry into view
        if 0 <= self._selected_idx < len(self._entries):
            self._labels[self._selected_idx].scroll_visible()

    def _fill_selected(self) -> None:
        """Fill the input with the highlighted entry (Tab)."""
        if not self._entries:
            return
        path, is_dir = self._entries[self._selected_idx]
        inp = self.query_one("#fp-input", Input)
        inp.value = str(path) + ("/" if is_dir else "")
        inp.cursor_position = len(inp.value)

    def _confirm(self) -> None:
        """Enter: expand directory or select file."""
        if self._entries:
            path, is_dir = self._entries[self._selected_idx]
            if is_dir:
                inp = self.query_one("#fp-input", Input)
                inp.value = str(path) + "/"
                inp.cursor_position = len(inp.value)
                return
            self.post_message(self.FileSelected(str(path.resolve())))
            return
        # No suggestions — try raw input path
        text = self.query_one("#fp-input", Input).value.strip()
        if text:
            p = Path(text).expanduser().resolve()
            if p.is_file():
                self.post_message(self.FileSelected(str(p)))
