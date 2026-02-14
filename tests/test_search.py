"""Tests for search engine."""

import tempfile
from pathlib import Path

from novel_tui.core.reader import BookReader
from novel_tui.core.search import BookSearcher
from novel_tui.db.models import Chapter


def _make_file(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb")
    f.write(content.encode("utf-8"))
    f.close()
    return Path(f.name)


def test_search_finds_matches():
    content = "第一章 开始\n小明去了学校。\n第二章 继续\n小明回到了家。"
    path = _make_file(content)

    part1 = "第一章 开始\n小明去了学校。\n"
    part2 = "第二章 继续\n小明回到了家。"

    chapters = [
        Chapter(book_id=1, index=0, title="第一章", byte_offset=0, length=len(part1.encode("utf-8"))),
        Chapter(book_id=1, index=1, title="第二章", byte_offset=len(part1.encode("utf-8")), length=len(part2.encode("utf-8"))),
    ]

    reader = BookReader(path, "utf-8")
    searcher = BookSearcher(reader, chapters)
    results = searcher.search("小明")

    assert len(results) == 2
    assert results[0].chapter_idx == 0
    assert results[1].chapter_idx == 1


def test_search_case_insensitive():
    content = "Hello World hello"
    path = _make_file(content)
    chapters = [Chapter(book_id=1, index=0, title="Ch1", byte_offset=0, length=len(content.encode("utf-8")))]

    reader = BookReader(path, "utf-8")
    searcher = BookSearcher(reader, chapters)
    results = searcher.search("hello")

    assert len(results) == 2


def test_search_no_results():
    content = "这是一段文字。"
    path = _make_file(content)
    chapters = [Chapter(book_id=1, index=0, title="Ch1", byte_offset=0, length=len(content.encode("utf-8")))]

    reader = BookReader(path, "utf-8")
    searcher = BookSearcher(reader, chapters)
    results = searcher.search("不存在的词")

    assert len(results) == 0
