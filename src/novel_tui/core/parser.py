"""Chapter parsing with regex + encoding detection."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from novel_tui.db.models import Book, Chapter

# Regex patterns for chapter detection
# Use .{0,50} to limit line length — chapter titles are short,
# body text lines mentioning "第X章" are much longer.
VOLUME_PATTERN = re.compile(
    r"^第[零一二三四五六七八九十百千\d]+[卷部集].{0,50}$", re.MULTILINE
)
CHAPTER_PATTERN = re.compile(
    r"^第[零一二三四五六七八九十百千万\d]+[章节回].{0,50}$", re.MULTILINE
)

ENCODINGS = ["utf-8", "gb18030", "gbk", "big5"]

ProgressCallback = Callable[[str], None]


def detect_encoding(raw: bytes) -> str:
    """Detect file encoding by trying common Chinese encodings.

    Uses a sample of the file (first 32KB) for speed.
    """
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    sample = raw[: min(len(raw), 32768)]
    for enc in ENCODINGS:
        try:
            sample.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def _raw_encoding(encoding: str) -> str:
    """Return a raw encoding name suitable for per-segment encode.

    'utf-8-sig' adds a BOM on every .encode() call, which breaks
    incremental offset calculation.  Map it to plain 'utf-8'.
    """
    return "utf-8" if encoding == "utf-8-sig" else encoding


def _find_byte_offsets(
    raw_bytes: bytes, titles: list[str], encoding: str
) -> list[int]:
    """Find byte offsets by searching for chapter titles directly in raw bytes.

    This avoids all char↔byte conversion issues (BOM, replacement chars, etc.)
    by doing a simple bytes.find() which is O(N) in C.
    """
    enc = _raw_encoding(encoding)
    byte_offsets: list[int] = []
    search_from = 0
    for title in titles:
        title_bytes = title.encode(enc, errors="replace")
        pos = raw_bytes.find(title_bytes, search_from)
        if pos != -1:
            byte_offsets.append(pos)
            search_from = pos + len(title_bytes)
        else:
            # Title not found — keep search_from moving forward
            byte_offsets.append(search_from)
    return byte_offsets


def parse_book(
    file_path: str | Path,
    progress: ProgressCallback | None = None,
) -> tuple[Book, list[Chapter]]:
    """Parse a txt file into a Book and its Chapters."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    _report = progress or (lambda _s: None)

    # ── Step 1: Read file once ──
    _report("读取文件...")
    raw_bytes = path.read_bytes()
    file_size = len(raw_bytes)

    # ── Step 2: Detect encoding (uses 32KB sample) ──
    _report("检测编码...")
    encoding = detect_encoding(raw_bytes)
    text = raw_bytes.decode(encoding, errors="replace")
    word_count = len(text)

    # ── Step 3: Regex match chapters ──
    _report("匹配章节标题...")
    matches: list[tuple[int, str, int]] = []  # (char_offset, title, level)
    for m in VOLUME_PATTERN.finditer(text):
        matches.append((m.start(), m.group().strip(), 1))
    for m in CHAPTER_PATTERN.finditer(text):
        matches.append((m.start(), m.group().strip(), 2))
    matches.sort(key=lambda x: x[0])

    # ── Step 4: Build chapters ──
    chapters: list[Chapter] = []

    if matches:
        _report(f"计算 {len(matches)} 个章节的偏移量...")
        # Find byte offsets by searching for titles in raw bytes directly
        titles = [title for _, title, _ in matches]
        byte_offsets = _find_byte_offsets(raw_bytes, titles, encoding)

        for i, (char_offset, title, level) in enumerate(matches):
            byte_offset = byte_offsets[i]
            if i + 1 < len(matches):
                byte_length = byte_offsets[i + 1] - byte_offset
            else:
                byte_length = file_size - byte_offset

            chapters.append(
                Chapter(
                    book_id=0,
                    index=i,
                    title=title,
                    level=level,
                    byte_offset=byte_offset,
                    length=byte_length,
                )
            )
    else:
        # No chapters found — split by line count
        _report("未检测到章节，按段落切分...")
        enc = _raw_encoding(encoding)
        lines = text.split("\n")
        chunk_size = 500
        if len(lines) <= chunk_size:
            chapters.append(
                Chapter(
                    book_id=0, index=0, title="全文", level=2,
                    byte_offset=0, length=file_size,
                )
            )
        else:
            byte_pos = 0
            seg_idx = 0
            newline_bytes = len("\n".encode(enc))
            for start in range(0, len(lines), chunk_size):
                end = min(start + chunk_size, len(lines))
                segment = "\n".join(lines[start:end])
                byte_length = len(segment.encode(enc, errors="replace"))
                if end < len(lines):
                    byte_length += newline_bytes
                first_line = lines[start].strip() or f"第 {seg_idx + 1} 段"
                title = first_line[:30] if len(first_line) > 30 else first_line
                chapters.append(
                    Chapter(
                        book_id=0, index=seg_idx, title=title, level=2,
                        byte_offset=byte_pos, length=byte_length,
                    )
                )
                byte_pos += byte_length
                seg_idx += 1

    _report(f"解析完成，共 {len(chapters)} 个章节")

    title = path.stem
    book = Book(
        title=title,
        file_path=str(path),
        file_size=file_size,
        encoding=encoding,
        word_count=word_count,
        chapter_count=len(chapters),
    )

    return book, chapters
