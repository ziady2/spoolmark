"""SubRip (.srt) parser."""

from __future__ import annotations

import re

from .cue import Cue
from .errors import ParseError, SubcueError
from .text_utils import strip_bom
from .track import Track

_INDEX_RE = re.compile(r"^\d+$")
_SRT_TIMESTAMP = r"\d+:\d{2}:\d{2}[,.]\d{1,3}"
_TIMESTAMP_PREFIX_RE = re.compile(rf"^\s*{_SRT_TIMESTAMP}")
_ARROW_RE = re.compile(rf"^\s*({_SRT_TIMESTAMP})\s*-->\s*({_SRT_TIMESTAMP})\s*$")


def _looks_like_timing(line: str) -> bool:
    stripped = line.strip()
    return bool(_TIMESTAMP_PREFIX_RE.match(stripped) or "-->" in stripped)


def _looks_like_cue_start(lines: list[str], position: int) -> bool:
    """Return whether a line after a blank run looks like a new SRT cue."""
    line = lines[position].strip()
    if _looks_like_timing(line):
        return True
    return bool(
        _INDEX_RE.fullmatch(line)
        and position + 1 < len(lines)
        and _looks_like_timing(lines[position + 1])
    )


def parse_srt_text(text: str, *, name: str = "SRT Track") -> Track:
    """Parse SRT text into a Track."""
    text = strip_bom(text).replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ParseError("empty SRT input")

    from .timing import parse_timecode

    lines = text.split("\n")
    cues: list[Cue] = []
    position = 0
    while position < len(lines):
        while position < len(lines) and not lines[position].strip():
            position += 1
        if position >= len(lines):
            break

        block_number = len(cues) + 1
        first_line = lines[position].strip()
        if _INDEX_RE.fullmatch(first_line):
            position += 1
            if position >= len(lines) or not lines[position].strip():
                raise ParseError(
                    f"block {block_number}: cue index is not followed by a timing line",
                    line=position + 1,
                )

        timing_line_number = position + 1
        timing_line = lines[position].strip()
        arrow_match = _ARROW_RE.fullmatch(timing_line)
        if arrow_match is None:
            raise ParseError(
                f"block {block_number}: malformed or missing timing line",
                line=timing_line_number,
            )
        position += 1

        text_lines: list[str] = []
        while position < len(lines):
            if lines[position].strip():
                text_lines.append(lines[position])
                position += 1
                continue

            blank_start = position
            while position < len(lines) and not lines[position].strip():
                position += 1
            if position >= len(lines):
                break
            if _looks_like_cue_start(lines, position):
                break
            text_lines.extend(lines[blank_start:position])

        cue_text = "\n".join(text_lines)
        if not cue_text.strip():
            raise ParseError(
                f"block {block_number}: cue text is empty",
                line=timing_line_number,
            )
        try:
            start = parse_timecode(arrow_match.group(1))
            end = parse_timecode(arrow_match.group(2))
            cues.append(Cue(index=len(cues) + 1, start=start, end=end, text=cue_text))
        except SubcueError as exc:
            raise ParseError(f"block {block_number}: {exc}", line=timing_line_number) from exc
    if not cues:
        raise ParseError("no valid cues found in SRT")
    return Track(name, cues=cues)


def parse_srt_file(path: str, **kw) -> Track:
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as exc:
        raise ParseError(f"cannot read file: {exc}") from exc
    return parse_srt_text(text, **kw)


def cues_to_srt(cues: list[Cue]) -> str:
    """Serialise cues back to SRT format."""
    from .timing import format_timecode

    parts: list[str] = []
    for i, cue in enumerate(cues, 1):
        tc = f"{format_timecode(cue.start)} --> {format_timecode(cue.end)}"
        parts.append(f"{i}\n{tc}\n{cue.text}")
    return "\n\n".join(parts) + "\n"
