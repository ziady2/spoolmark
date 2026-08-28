"""Markup-aware word wrapping for subtitle display.

The wrapper treats HTML and ASS override blocks as zero-width markup.  It
never truncates or splits a word.  When all content cannot fit inside the
requested rectangle, the final line contains the remaining words and is
allowed to exceed ``max_width``; the result still never exceeds
``max_lines``.  Callers that can create more cues (for example
``segment_text``) can avoid that fallback by distributing the words over
additional cues.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable, List, Optional, Sequence, Tuple

# Starting a line with one of these short words is usually visually awkward.
# This is a soft preference: preserving content and respecting the dimensions
# take precedence.
_NO_BREAK_BEFORE = {
    "a",
    "an",
    "and",
    "at",
    "but",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
}

_HTML_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9:_-]*")
_VOID_HTML_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def wrap_subtitle(
    text: str,
    max_width: int = 42,
    max_lines: int = 2,
) -> str:
    """Wrap *text* without dropping words or splitting markup blocks.

    Existing newlines are retained when they already satisfy both limits.
    Otherwise they are treated as ordinary whitespace and the text is
    rebalanced.  HTML tags that span a newly-created line boundary are closed
    at the end of the line and reopened on the next one.  ASS ``{...}``
    blocks remain atomic.

    If the limits are mathematically impossible (an overlong word, or more
    content than ``max_width * max_lines`` can hold), all overflow is placed
    on the last line.  Thus content is lossless and ``max_lines`` is a hard
    limit, while ``max_width`` is best-effort for impossible input.
    """
    _validate_text(text)
    _validate_limits(max_width, max_lines)

    existing_lines = text.splitlines()
    if not existing_lines:
        return text
    if len(existing_lines) <= max_lines and all(
        _visible_length(line) <= max_width for line in existing_lines
    ):
        return text

    words = _markup_words(text)
    if not words:
        return text

    lines = _balance_lines(words, max_width, max_lines)
    return "\n".join(_balance_html_fragments(lines))


def check_line_lengths(
    text: str,
    max_width: int = 42,
    max_lines: int = 2,
) -> dict:
    """Report whether *text* conforms to the visible line limits.

    Markup does not contribute to a line's displayed length.  Empty strings
    have zero lines; explicit blank lines are counted in the same way as
    ``str.splitlines()``.
    """
    _validate_text(text)
    _validate_limits(max_width, max_lines)

    lines = text.splitlines()
    lengths = [_visible_length(line) for line in lines]
    issues: List[str] = []
    if len(lines) > max_lines:
        issues.append(f"too many lines: {len(lines)} > {max_lines}")
    for number, length in enumerate(lengths, 1):
        if length > max_width:
            issues.append(f"line {number} too long: {length} > {max_width}")
    return {
        "conformant": not issues,
        "line_count": len(lines),
        "max_line_length": max(lengths, default=0),
        "issues": issues,
    }


def balance_score(text: str) -> float:
    """Return a visible-line balance score clamped to ``0.0 .. 1.0``.

    One line (including an empty string) is considered perfectly balanced.
    Tags are ignored because they occupy no display width.
    """
    _validate_text(text)
    lines = text.splitlines()
    if len(lines) < 2:
        return 1.0

    lengths = [_visible_length(line) for line in lines]
    average = sum(lengths) / len(lengths)
    if average == 0:
        return 1.0
    variance = sum((length - average) ** 2 for length in lengths) / len(lengths)
    raw_score = 1.0 - variance / (average**2)
    return round(max(0.0, min(1.0, raw_score)), 3)


def rebalance_lines(text: str, max_width: int = 42) -> str:
    """Flatten and re-wrap *text* into at most two balanced lines."""
    _validate_text(text)
    _validate_limits(max_width, 2)
    # ``_markup_words`` knows that spaces inside ``<font color=...>`` are not
    # word boundaries; a plain ``text.split()`` would corrupt such a tag.
    flat = " ".join(_markup_words(text))
    return wrap_subtitle(flat, max_width=max_width, max_lines=2)


def _validate_text(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")


def _validate_limits(max_width: int, max_lines: int) -> None:
    if isinstance(max_width, bool) or not isinstance(max_width, int) or max_width <= 0:
        raise ValueError("max_width must be a positive integer")
    if isinstance(max_lines, bool) or not isinstance(max_lines, int) or max_lines <= 0:
        raise ValueError("max_lines must be a positive integer")


def _visible_length(text: str) -> int:
    """Return the rendered character count of a tagged fragment."""
    return len(_visible_text(text))


def _visible_text(text: str) -> str:
    """Remove markup using the same quote-aware lexer used for wrapping."""
    return "".join(token for token in _markup_tokens(text) if not _is_markup(token))


def _markup_tokens(text: str) -> List[str]:
    """Lex text into markup, whitespace, and visible tokens.

    The small scanner intentionally understands quoted HTML attributes, so a
    value such as ``title="a > b"`` is kept in one token.  Malformed opening
    delimiters are treated as visible text rather than swallowing the rest of
    the subtitle.
    """
    tokens: List[str] = []
    position = 0
    length = len(text)
    while position < length:
        character = text[position]
        if character == "<":
            end = _html_tag_end(text, position)
            if end is not None:
                tokens.append(text[position:end])
                position = end
                continue
        elif character == "{":
            closing = text.find("}", position + 1)
            if closing >= 0:
                tokens.append(text[position : closing + 1])
                position = closing + 1
                continue

        if character.isspace():
            end = position + 1
            while end < length and text[end].isspace():
                end += 1
            tokens.append(text[position:end])
            position = end
            continue

        end = position + 1
        while end < length and not text[end].isspace() and text[end] not in "<{":
            end += 1
        tokens.append(text[position:end])
        position = end
    return tokens


def _html_tag_end(text: str, start: int) -> Optional[int]:
    quote: Optional[str] = None
    position = start + 1
    while position < len(text):
        character = text[position]
        if quote is not None:
            if character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == ">":
            return position + 1
        position += 1
    return None


def _is_markup(token: str) -> bool:
    return (token.startswith("<") and token.endswith(">")) or (
        token.startswith("{") and token.endswith("}")
    )


def _html_tag_info(token: str) -> Optional[Tuple[str, bool, bool]]:
    """Return ``(name, closing, self_closing)`` for an HTML tag token."""
    if not (token.startswith("<") and token.endswith(">")):
        return None
    content = token[1:-1].strip()
    if not content or content.startswith(("!", "?")):
        return None
    closing = content.startswith("/")
    if closing:
        content = content[1:].lstrip()
    self_closing = content.endswith("/")
    if self_closing:
        content = content[:-1].rstrip()
    match = _HTML_NAME_RE.match(content)
    if match is None:
        return None
    return match.group(0).lower(), closing, self_closing


def _markup_words(text: str) -> List[str]:
    """Return whitespace-delimited words while keeping markup intact.

    Tag-only runs are attached to the nearest word.  This avoids producing
    zero-width lines and preserves closing tags that appear after whitespace.
    """
    words: List[str] = []
    current: List[str] = []
    pending: List[str] = []

    def flush() -> None:
        if not current:
            return
        raw = "".join(current)
        if _visible_length(raw) > 0:
            words.append("".join(pending) + raw)
            pending.clear()
        else:
            pending.extend(current)
        current.clear()

    for token in _markup_tokens(text):
        if token.isspace():
            flush()
        else:
            current.append(token)
    flush()

    if pending:
        markup = "".join(pending)
        if words:
            words[-1] += markup
        else:
            words.append(markup)
    return words


def _line_length(words: Sequence[str]) -> int:
    if not words:
        return 0
    return sum(_visible_length(word) for word in words) + len(words) - 1


def _awkward_line_start(word: str) -> bool:
    visible = _visible_text(word).strip().lower()
    visible = visible.strip(".,!?;:()[]{}\"'")
    return visible in _NO_BREAK_BEFORE


def _strict_partition(words: Sequence[str], max_width: int, max_lines: int) -> Optional[List[str]]:
    """Find a balanced, fully conforming partition, if one exists."""
    if not words:
        return []
    if any(_visible_length(word) > max_width for word in words):
        return None

    word_count = len(words)
    prefix = [0]
    for word in words:
        prefix.append(prefix[-1] + _visible_length(word))

    def width(start: int, end: int) -> int:
        return prefix[end] - prefix[start] + max(0, end - start - 1)

    for line_count in range(1, min(max_lines, word_count) + 1):
        target = width(0, word_count) / line_count

        @lru_cache(maxsize=None)
        def solve(start: int, lines_left: int) -> Optional[Tuple[float, Tuple[int, ...]]]:
            remaining_words = word_count - start
            if remaining_words < lines_left:
                return None
            if lines_left == 1:
                line_width = width(start, word_count)
                if line_width > max_width:
                    return None
                return ((line_width - target) ** 2, (word_count,))

            best: Optional[Tuple[float, Tuple[int, ...]]] = None
            latest_end = word_count - lines_left + 1
            for end in range(start + 1, latest_end + 1):
                line_width = width(start, end)
                if line_width > max_width:
                    break
                remainder = solve(end, lines_left - 1)
                if remainder is None:
                    continue
                awkward_penalty = target if _awkward_line_start(words[end]) else 0.0
                score = (line_width - target) ** 2 + awkward_penalty + remainder[0]
                candidate = (score, (end,) + remainder[1])
                if best is None or candidate[0] < best[0]:
                    best = candidate
            return best

        solution = solve(0, line_count)
        if solution is None:
            continue
        lines: List[str] = []
        start = 0
        for end in solution[1]:
            lines.append(" ".join(words[start:end]))
            start = end
        return lines
    return None


def _overflow_partition(words: Sequence[str], max_width: int, max_lines: int) -> List[str]:
    """Preserve impossible content, using the final line as overflow."""
    if not words:
        return []
    if max_lines == 1:
        return [" ".join(words)]

    lines: List[str] = []
    position = 0
    # Reserve one line for all remaining content.  Earlier lines are always
    # filled conformantly when possible.
    while position < len(words) and len(lines) < max_lines - 1:
        end = position + 1
        if _visible_length(words[position]) > max_width:
            lines.append(words[position])
            position = end
            continue
        while end < len(words) and _line_length(words[position : end + 1]) <= max_width:
            end += 1
        lines.append(" ".join(words[position:end]))
        position = end
    if position < len(words):
        lines.append(" ".join(words[position:]))
    return lines


def _balance_lines(words: List[str], max_width: int, max_lines: int) -> List[str]:
    """Distribute words without exceeding ``max_lines`` or losing text."""
    strict = _strict_partition(words, max_width, max_lines)
    if strict is not None:
        return strict
    return _overflow_partition(words, max_width, max_lines)


def _balance_html_fragments(fragments: Iterable[str]) -> List[str]:
    """Close and reopen HTML tags at boundaries between fragments.

    The logical stack deliberately ignores ASS override blocks.  They remain
    byte-for-byte intact and are never split, but ASS state is not guessed or
    synthesized because arbitrary override blocks do not have reliable
    inverses.
    """
    active: List[Tuple[str, str]] = []
    balanced: List[str] = []
    for fragment in fragments:
        reopened = "".join(opening for _name, opening in active)
        for token in _markup_tokens(fragment):
            if not _is_markup(token) or token.startswith("{"):
                continue
            info = _html_tag_info(token)
            if info is None:
                continue
            name, closing, self_closing = info
            if closing:
                for position in range(len(active) - 1, -1, -1):
                    if active[position][0] == name:
                        del active[position:]
                        break
            elif not self_closing and name not in _VOID_HTML_TAGS:
                active.append((name, token))
        closings = "".join(f"</{name}>" for name, _opening in reversed(active))
        balanced.append(reopened + fragment + closings)
    return balanced


def _truncate_words(words: List[str], max_width: int) -> str:
    """Return the longest whole-word prefix that fits ``max_width``.

    Kept as an internal compatibility helper.  A first overlong word is
    returned whole, matching the module's never-split policy.
    """
    _validate_limits(max_width, 1)
    result: List[str] = []
    for word in words:
        candidate = result + [word]
        if result and _line_length(candidate) > max_width:
            break
        result.append(word)
        if _line_length(result) > max_width:
            break
    return " ".join(result)
