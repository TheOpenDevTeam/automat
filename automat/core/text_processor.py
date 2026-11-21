"""
Text processing business logic — transformations, find/replace, statistics,
and regex matching. No Qt dependencies; testable without QApplication.
"""

import re
import collections
from dataclasses import dataclass
from typing import Optional


@dataclass
class TextStats:
    chars: int
    words: int
    lines: int
    unique_words: int
    top_words: list[tuple[str, int]]


@dataclass
class FindResult:
    matches: list[tuple[int, int]]  # (start, end) positions
    count: int


class TextProcessor:
    """Pure text processing logic. All methods take text in, return text/results out."""

    # ── Transformations ──────────────────────────────────────────────

    @staticmethod
    def transform(text: str, func) -> str:
        """Apply a string function (upper, lower, title, strip) to whole text."""
        return func(text)

    @staticmethod
    def sort_lines(text: str, ascending: bool = True) -> str:
        lines = text.splitlines()
        lines.sort(reverse=not ascending)
        return "\n".join(lines)

    @staticmethod
    def dedup_lines(text: str) -> str:
        seen: list[str] = []
        for line in text.splitlines():
            if line not in seen:
                seen.append(line)
        return "\n".join(seen)

    @staticmethod
    def reverse_text(text: str) -> str:
        return text[::-1]

    # ── Find / Replace ───────────────────────────────────────────────

    @staticmethod
    def find(text: str, pattern: str, regex: bool = False,
             ignore_case: bool = False) -> FindResult:
        if not pattern:
            return FindResult(matches=[], count=0)
        flags = re.IGNORECASE if ignore_case else 0
        if regex:
            try:
                compiled = re.compile(pattern, flags)
            except re.error:
                return FindResult(matches=[], count=0)
        else:
            compiled = re.compile(re.escape(pattern), flags)
        matches = [(m.start(), m.end()) for m in compiled.finditer(text)]
        return FindResult(matches=matches, count=len(matches))

    @staticmethod
    def replace(text: str, find_text: str, replace_text: str,
                regex: bool = False, ignore_case: bool = False) -> str:
        if not find_text:
            return text
        flags = re.IGNORECASE if ignore_case else 0
        if regex:
            try:
                return re.sub(find_text, replace_text, text, flags=flags)
            except re.error:
                return text
        return text.replace(find_text, replace_text)

    # ── Statistics ───────────────────────────────────────────────────

    @staticmethod
    def stats(text: str) -> TextStats:
        chars = len(text)
        words_list = text.split() if text.strip() else []
        words = len(words_list)
        lines = text.count("\n") + (1 if text else 0)
        unique = len(set(words_list)) if words_list else 0
        counter = collections.Counter(words_list)
        top_words = counter.most_common(20)
        return TextStats(
            chars=chars, words=words, lines=lines,
            unique_words=unique, top_words=top_words,
        )

    # ── Regex tester ─────────────────────────────────────────────────

    @staticmethod
    def run_regex(pattern: str, test_text: str, flags: int = 0):
        """Returns (status_message, output_text, match_count, match_positions)."""
        if not pattern:
            return ("", "", 0, [])
        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            return (f"Invalid regex: {e}", "", 0, [])

        if not test_text:
            return ("", "", 0, [])

        matches = list(compiled.finditer(test_text))
        count = len(matches)

        if count == 0:
            return ("Found 0 match(es)", "", 0, [])

        lines = []
        positions = []
        for idx, m in enumerate(matches, 1):
            start, end = m.start(), m.end()
            matched_text = m.group(0)
            positions.append((start, end))
            lines.append(f"Match #{idx}  [pos {start}\u2013{end}]: {matched_text!r}")
            if m.lastindex and m.lastindex > 0:
                if m.groupdict():
                    for name, val in m.groupdict().items():
                        if val is not None:
                            lines.append(f"  [{name}] = {val!r}")
                for g in range(1, m.lastindex + 1):
                    gname = compiled.groupindex.get(g, None)
                    if gname:
                        lines.append(f"  [{gname}] = {m.group(g)!r}")
                    else:
                        lines.append(f"  group {g}: {m.group(g)!r}")
            lines.append("")

        return (f"Found {count} match(es)", "\n".join(lines), count, positions)
