"""Tests for book reader."""

import tempfile
from pathlib import Path

from novel_tui.core.reader import BookReader
from novel_tui.db.models import Chapter


def _make_file(content: str, encoding: str = "utf-8") -> Path:
    f = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb")
    f.write(content.encode(encoding))
    f.close()
    return Path(f.name)


def test_read_chapter():
    content = "第一章 开始\n这是第一章。\n第二章 继续\n这是第二章。"
    path = _make_file(content)

    # Calculate offsets
    part1 = "第一章 开始\n这是第一章。\n"
    part2 = "第二章 继续\n这是第二章。"
    offset1 = 0
    len1 = len(part1.encode("utf-8"))
    offset2 = len1
    len2 = len(part2.encode("utf-8"))

    reader = BookReader(path, "utf-8")
    ch1 = Chapter(book_id=1, index=0, title="第一章", byte_offset=offset1, length=len1)
    ch2 = Chapter(book_id=1, index=1, title="第二章", byte_offset=offset2, length=len2)

    text1 = reader.read_chapter(ch1)
    assert "第一章 开始" in text1
    assert "这是第一章" in text1

    text2 = reader.read_chapter(ch2)
    assert "第二章 继续" in text2
    assert "这是第二章" in text2


def test_read_range():
    content = "Hello World"
    path = _make_file(content)
    reader = BookReader(path, "utf-8")
    assert reader.read_range(6, 5) == "World"
