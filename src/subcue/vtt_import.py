"""WebVTT (.vtt) parser."""

from __future__ import annotations

import re

from .cue import Cue
from .errors import ParseError, SubcueError
from .text_utils import strip_bom
from .track import Track

_VTT_TIMESTAMP = r"(?:\d+:\d{2}:\d{2}|\d{2}:\d{2})[.]\d{1,3}"
_TIMESTAMP_PREFIX_RE = re.compile(rf"^\s*{_VTT_TIMESTAMP}")
_ARROW_RE = re.compile(rf"^\s*({_VTT_TIMESTAMP})\s*-->\s*({_VTT_TIMESTAMP})(?:[ \t]+.*)?$")
_HEADER_RE = re.compile(r"^WEBVTT(?:[ \t].*)?$", re.IGNORECASE)


def _is_auxiliary_block(line: str) -> bool:
    """Return whether *line* starts a permitted non-cue WebVTT block."""
    stripped = line.strip()
    upper = stripped.upper()
    return bool(
        upper == "STYLE"
        or upper == "REGION"
        or upper == "NOTE"
        or upper.startswith("NOTE ")
        or upper.startswith("NOTE\t")
        or upper.startswith("X-TIMESTAMP-MAP=")
    )


def _looks_like_timing(line: str) -> bool:
    stripped = line.strip()
    return bool(_TIMESTAMP_PREFIX_RE.match(stripped) or "-->" in stripped)


def _looks_like_block_start(lines: list[str], position: int) -> bool:
    """Return whether a line after a blank run begins a VTT block."""
    line = lines[position]
    if _is_auxiliary_block(line) or _looks_like_timing(line):
        return True
    return position + 1 < len(lines) and _looks_like_timing(lines[position + 1])


def parse_vtt_text(text: str, *, name: str = "VTT Track") -> Track:
    text = strip_bom(text).replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ParseError("empty VTT input")

    from .timing import parse_timecode

    lines = text.split("\n")
    position = 0
    while position < len(lines) and not lines[position].strip():
        position += 1
    if position >= len(lines) or not _HEADER_RE.fullmatch(lines[position].strip()):
        raise ParseError("missing WEBVTT header")
    position += 1

    # Everything else in the initial header block is metadata.  A blank line
    # is required before the first cue or auxiliary block.
    while position < len(lines) and lines[position].strip():
        position += 1

    cues: list[Cue] = []
    while position < len(lines):
        while position < len(lines) and not lines[position].strip():
            position += 1
        if position >= len(lines):
            break

        if _is_auxiliary_block(lines[position]):
            position += 1
            while position < len(lines) and lines[position].strip():
                position += 1
            continue

        block_number = len(cues) + 1
        timing_position = position
        arrow_match = _ARROW_RE.fullmatch(lines[timing_position].strip())
        if arrow_match is None and position + 1 < len(lines):
            possible_timing = lines[position + 1].strip()
            if _looks_like_timing(possible_timing):
                timing_position = position + 1
                arrow_match = _ARROW_RE.fullmatch(possible_timing)
        if arrow_match is None:
            candidate_line = lines[timing_position].strip()
            detail = (
                "malformed timing line"
                if _looks_like_timing(candidate_line)
                else "missing timing line"
            )
            raise ParseError(
                f"block {block_number}: {detail}",
                line=timing_position + 1,
            )
        position = timing_position + 1

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
            if _looks_like_block_start(lines, position):
                break
            text_lines.extend(lines[blank_start:position])

        cue_text = "\n".join(text_lines)
        if not cue_text.strip():
            raise ParseError(
                f"block {block_number}: cue text is empty",
                line=timing_position + 1,
            )
        try:
            start = parse_timecode(arrow_match.group(1))
            end = parse_timecode(arrow_match.group(2))
            cues.append(Cue(index=len(cues) + 1, start=start, end=end, text=cue_text))
        except SubcueError as exc:
            raise ParseError(f"block {block_number}: {exc}", line=timing_position + 1) from exc
    if not cues:
        raise ParseError("no valid cues found in VTT")
    return Track(name, cues=cues)


def parse_vtt_file(path: str, **kw) -> Track:
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as exc:
        raise ParseError(f"cannot read file: {exc}") from exc
    return parse_vtt_text(text, **kw)


def cues_to_vtt(cues: list[Cue]) -> str:
    from .timing import format_timecode_vtt

    parts = ["WEBVTT"]
    for i, cue in enumerate(cues, 1):
        tc = f"{format_timecode_vtt(cue.start)} --> {format_timecode_vtt(cue.end)}"
        parts.append(f"{i}\n{tc}\n{cue.text}")
    return "\n\n".join(parts) + "\n"
