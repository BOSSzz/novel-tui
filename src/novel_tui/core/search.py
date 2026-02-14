"""Full-text search engine."""

from __future__ import annotations

from dataclasses import dataclass

from novel_tui.core.reader import BookReader
from novel_tui.db.models import Chapter


@dataclass
class SearchResult:
    chapter_idx: int
    chapter_title: str
    char_offset: int  # offset within chapter text
    context: str      # surrounding text snippet


class BookSearcher:
    """Searches through book chapters for text matches."""

    def __init__(self, reader: BookReader, chapters: list[Chapter]) -> None:
        self.reader = reader
        self.chapters = chapters

    def search(self, query: str, *, case_sensitive: bool = False) -> list[SearchResult]:
        """Search all chapters for the given query string."""
        results: list[SearchResult] = []
        for chapter in self.chapters:
            try:
                text = self.reader.read_chapter(chapter)
            except FileNotFoundError:
                continue

            search_text = text if case_sensitive else text.lower()
            search_query = query if case_sensitive else query.lower()

            start = 0
            while True:
                pos = search_text.find(search_query, start)
                if pos == -1:
                    break
                # Extract context (40 chars before and after)
                ctx_start = max(0, pos - 40)
                ctx_end = min(len(text), pos + len(query) + 40)
                context = text[ctx_start:ctx_end].replace("\n", " ")
                if ctx_start > 0:
                    context = "..." + context
                if ctx_end < len(text):
                    context = context + "..."

                results.append(
                    SearchResult(
                        chapter_idx=chapter.index,
                        chapter_title=chapter.title,
                        char_offset=pos,
                        context=context,
                    )
                )
                start = pos + 1
        return results
