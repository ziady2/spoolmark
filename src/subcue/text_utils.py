"""Text manipulation utilities for subtitle content."""

from __future__ import annotations

import re
import unicodedata
from typing import Sequence

_TAG_RE = re.compile(r"<[^>]+>")
_ASS_TAG_RE = re.compile(r"\{[^}]*\}")
_MULTI_SPACE = re.compile(r"[ \t]+")


def strip_html_tags(text: str) -> str:
    """Remove HTML tags like ``<b>``, ``<i>``, ``<font color=...>``."""
    return _TAG_RE.sub("", text)


def strip_ass_tags(text: str) -> str:
    """Remove ASS override tags like ``{\\b1}``."""
    return _ASS_TAG_RE.sub("", text)


def strip_all_tags(text: str) -> str:
    """Remove both HTML and ASS tags."""
    return strip_ass_tags(strip_html_tags(text))


def normalize_whitespace(text: str) -> str:
    return _MULTI_SPACE.sub(" ", text).strip()


def strip_bom(text: str) -> str:
    if text.startswith("\ufeff"):
        return text[1:]
    return text


def collapse_newlines(text: str) -> str:
    """Collapse multiple blank lines into a single newline."""
    lines = text.splitlines()
    result: list[str] = []
    prev_blank = False
    for line in lines:
        if not line.strip():
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    return "\n".join(result)


def word_count(text: str) -> int:
    clean = strip_all_tags(text)
    return len(clean.split())


def char_count(text: str, *, exclude_spaces: bool = False) -> int:
    clean = strip_all_tags(text)
    if exclude_spaces:
        clean = clean.replace(" ", "").replace("\n", "")
    return len(clean)


def line_count(text: str) -> int:
    return len([line for line in text.splitlines() if line.strip()])


def truncate(text: str, length: int = 80, suffix: str = "...") -> str:
    if length < len(suffix):
        return suffix[:length]
    if len(text) <= length:
        return text
    return text[: length - len(suffix)].rstrip() + suffix


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


def wrap_lines(text: str, width: int = 42) -> list[str]:
    """Word-wrap subtitle text to *width* characters per line."""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        if current and length + len(word) + 1 > width:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += len(word) + (1 if len(current) > 1 else 0)
    if current:
        lines.append(" ".join(current))
    return lines


def extract_speaker(text: str) -> tuple[str, str]:
    """Extract speaker prefix like ``JOHN: Hello`` -> (``JOHN``, ``Hello``)."""
    m = re.match(r"^([A-Z][A-Z0-9 _.-]{0,30}):\s*(.+)", text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", text


def join_and(items: Sequence[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def pad_right(text: str, width: int) -> str:
    return text + " " * max(0, width - len(text))


def pad_left(text: str, width: int) -> str:
    return " " * max(0, width - len(text)) + text
