"""Tests for chapter parser."""

import tempfile
from pathlib import Path

from novel_tui.core.parser import detect_encoding, parse_book


def _make_novel(content: str, encoding: str = "utf-8") -> Path:
    """Create a temporary novel file."""
    f = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb")
    f.write(content.encode(encoding))
    f.close()
    return Path(f.name)


def test_detect_encoding_utf8():
    raw = "Hello 你好".encode("utf-8")
    assert detect_encoding(raw) == "utf-8"


def test_detect_encoding_gbk():
    raw = "Hello 你好".encode("gbk")
    enc = detect_encoding(raw)
    assert enc in ("gb18030", "gbk")


def test_parse_chapters():
    content = """第一章 开端

这是第一章的内容。

第二章 发展

这是第二章的内容。

第三章 结尾

这是第三章的内容。
"""
    path = _make_novel(content)
    book, chapters = parse_book(path)

    assert book.title == path.stem
    assert book.chapter_count == 3
    assert len(chapters) == 3
    assert chapters[0].title == "第一章 开端"
    assert chapters[1].title == "第二章 发展"
    assert chapters[2].title == "第三章 结尾"
    assert chapters[0].level == 2
    assert all(ch.byte_offset >= 0 for ch in chapters)
    assert all(ch.length > 0 for ch in chapters)


def test_parse_with_volumes():
    content = """第一卷 起始

第一章 开始

他翻开了第一章的内容，仔细地阅读起来，发现里面的故事非常精彩，让他欲罢不能。

第二章 继续

她在看第二章内容的时候不禁感叹，人生就像一本书，每一页都是新的故事和经历。

第二卷 终结

第三章 结束

故事到了第三章结尾的时候，所有的线索终于汇聚在一起，真相大白于天下，读者们纷纷拍手称快。
"""
    path = _make_novel(content)
    book, chapters = parse_book(path)

    assert book.chapter_count == 5
    # Check volume levels
    volumes = [ch for ch in chapters if ch.level == 1]
    chapter_items = [ch for ch in chapters if ch.level == 2]
    assert len(volumes) == 2
    assert len(chapter_items) == 3


def test_parse_no_chapters_short():
    content = "这是一本没有章节的小说。只有一大段文字。"
    path = _make_novel(content)
    book, chapters = parse_book(path)

    assert book.chapter_count == 1
    assert chapters[0].title == "全文"


def test_parse_no_chapters_long():
    """Large file without chapter markers should be split by lines."""
    lines = [f"这是第{i}行的内容，故事还在继续。" for i in range(1200)]
    content = "\n".join(lines)
    path = _make_novel(content)
    book, chapters = parse_book(path)

    assert book.chapter_count == 3  # 1200 lines / 500 per chunk = 3 segments
    assert all(ch.length > 0 for ch in chapters)
    assert all(ch.byte_offset >= 0 for ch in chapters)


def test_parse_no_space_chapters():
    content = """第一章天降奇缘

这是第一章的内容，故事就这样开始了，一切都显得那么自然而然，仿佛命运早已注定。

第二章风云变幻

这是第二章的内容。

第三章尘埃落定

这是第三章的内容。
"""
    path = _make_novel(content)
    book, chapters = parse_book(path)

    assert book.chapter_count == 3
    assert chapters[0].title == "第一章天降奇缘"
    assert chapters[1].title == "第二章风云变幻"


def test_parse_numeric_chapters():
    content = """第1章 开始

内容一。

第2章 中间

内容二。

第3章 结束

内容三。
"""
    path = _make_novel(content)
    book, chapters = parse_book(path)

    assert book.chapter_count == 3
    assert chapters[0].title == "第1章 开始"
