"""Advanced SubStation Alpha (.ass/.ssa) parser."""

from __future__ import annotations

from .cue import Cue
from .errors import ParseError, SubcueError
from .style import Style
from .text_utils import strip_bom
from .track import Track

_DEFAULT_EVENT_FIELDS = (
    "layer",
    "start",
    "end",
    "style",
    "name",
    "marginl",
    "marginr",
    "marginv",
    "effect",
    "text",
)


def parse_ass_text(text: str, *, name: str = "ASS Track") -> Track:
    text = strip_bom(text).replace("\r\n", "\n").strip()
    if not text:
        raise ParseError("empty ASS input")
    cues: list[Cue] = []
    from .timing import parse_timecode

    in_events = False
    event_fields = list(_DEFAULT_EVENT_FIELDS)
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_events = stripped.casefold() == "[events]"
            continue
        if in_events and stripped.casefold().startswith("format:"):
            candidate_fields = [
                field.strip().casefold() for field in stripped.split(":", 1)[1].split(",")
            ]
            if {"start", "end", "text"}.issubset(candidate_fields):
                event_fields = candidate_fields
            continue
        if not stripped.casefold().startswith("dialogue:"):
            continue
        raw_values = stripped.split(":", 1)[1].lstrip()
        values = raw_values.split(",", len(event_fields) - 1)
        if len(values) != len(event_fields):
            raise ParseError("malformed Dialogue line", line=lineno)
        event = dict(zip(event_fields, values))
        try:
            start = parse_timecode(event["start"].strip())
            end = parse_timecode(event["end"].strip())
        except (KeyError, SubcueError) as exc:
            raise ParseError(f"invalid Dialogue timing: {exc}", line=lineno) from exc
        style_name = event.get("style", "").strip()
        speaker = event.get("name", "").strip()
        raw_text = event["text"].strip()
        clean = raw_text.replace("\\N", "\n").replace("\\n", "\n")
        if not clean.strip():
            continue
        try:
            cues.append(
                Cue(
                    index=len(cues) + 1,
                    start=start,
                    end=end,
                    text=clean,
                    speaker=speaker,
                    style=style_name,
                )
            )
        except SubcueError as exc:
            raise ParseError(f"invalid Dialogue cue: {exc}", line=lineno) from exc
    if not cues:
        raise ParseError("no Dialogue lines found in ASS")
    return Track(name, cues=cues)


def parse_ass_styles(text: str) -> list[Style]:
    """Extract Style definitions from ASS text."""
    text = strip_bom(text).replace("\r\n", "\n")
    styles: list[Style] = []
    in_styles = False
    format_keys: list[str] = []
    for line in text.splitlines():
        if line.strip().lower() == "[v4+ styles]" or line.strip().lower() == "[v4 styles]":
            in_styles = True
            continue
        if in_styles and line.startswith("Format:"):
            format_keys = [k.strip().lower() for k in line[7:].split(",")]
            continue
        if in_styles and line.startswith("Style:"):
            values = [v.strip() for v in line[6:].split(",")]
            if format_keys and len(values) >= len(format_keys):
                d = dict(zip(format_keys, values))
                styles.append(
                    Style(
                        name=d.get("name", "Default"),
                        font_name=d.get("fontname", "Arial"),
                        font_size=int(d.get("fontsize", "20")),
                        bold=d.get("bold", "0") != "0",
                        italic=d.get("italic", "0") != "0",
                    )
                )
        if line.startswith("[") and in_styles and "styles" not in line.lower():
            break
    return styles


def parse_ass_file(path: str, **kw) -> Track:
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as exc:
        raise ParseError(f"cannot read file: {exc}") from exc
    return parse_ass_text(text, **kw)
