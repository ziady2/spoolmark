"""Plain text subtitle parser (custom tab/pipe-delimited format).

Format::

    00:00:01.000 --> 00:00:04.000 | Hello, world!
    00:00:05.500 --> 00:00:08.200 | Second line here.
"""

from __future__ import annotations

import re

from .cue import Cue
from .errors import ParseError, SubcueError
from .text_utils import strip_bom
from .track import Track

_LINE_RE = re.compile(r"(\d[\d:.,-]+)\s*(?:-->|->|\|)\s*(\d[\d:.,-]+)\s*\|?\s*(.+)")


def parse_txt_text(text: str, *, name: str = "TXT Track") -> Track:
    text = strip_bom(text).strip()
    if not text:
        raise ParseError("empty text input")
    from .timing import parse_timecode

    cues: list[Cue] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE_RE.match(line)
        if not m:
            raise ParseError("bad line format", line=lineno)
        try:
            start = parse_timecode(m.group(1))
            end = parse_timecode(m.group(2))
            cue_text = _unescape_text(m.group(3).strip())
            cues.append(Cue(index=len(cues) + 1, start=start, end=end, text=cue_text))
        except SubcueError as exc:
            raise ParseError(str(exc), line=lineno) from exc
    if not cues:
        raise ParseError("no valid cues found")
    return Track(name, cues=cues)


def parse_txt_file(path: str, **kw) -> Track:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise ParseError(f"cannot read file: {exc}") from exc
    return parse_txt_text(text, **kw)


def cues_to_txt(cues: list[Cue]) -> str:
    from .timing import format_timecode_vtt

    lines: list[str] = []
    for cue in cues:
        text = _escape_text(cue.text)
        lines.append(
            f"{format_timecode_vtt(cue.start)} --> {format_timecode_vtt(cue.end)} | {text}"
        )
    return "\n".join(lines) + "\n"


def _escape_text(text: str) -> str:
    """Escape backslashes and embedded newlines for the line-based format."""
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalised.replace("\\", "\\\\").replace("\n", r"\N")


def _unescape_text(text: str) -> str:
    """Decode line-format escapes without losing literal backslashes."""
    result: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char != "\\" or index + 1 >= len(text):
            result.append(char)
            index += 1
            continue
        following = text[index + 1]
        if following in {"N", "n"}:
            result.append("\n")
        elif following == "\\":
            result.append("\\")
        else:
            result.extend(("\\", following))
        index += 2
    return "".join(result)
