"""JSON subtitle import/export."""

from __future__ import annotations

import json

from .cue import Cue
from .errors import ParseError, ValidationError
from .text_utils import strip_bom
from .track import Track


def parse_json_text(text: str, *, name: str = "JSON Track") -> Track:
    text = strip_bom(text).strip()
    if not text:
        raise ParseError("empty JSON input")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParseError(f"invalid JSON: {exc}", line=exc.lineno) from exc
    language = ""
    created = ""
    if isinstance(data, dict) and "cues" in data:
        items = data["cues"]
        name = str(data.get("name", name))
        language = str(data.get("language", ""))
        created = str(data.get("created", ""))
    elif isinstance(data, list):
        items = data
    else:
        raise ParseError("expected object with 'cues' key or array")
    if not isinstance(items, list):
        raise ParseError("'cues' must be an array")
    cues: list[Cue] = []
    for i, raw in enumerate(items, 1):
        if not isinstance(raw, dict):
            raise ParseError(f"item {i}: expected object", line=i)
        try:
            cues.append(
                Cue(
                    index=int(raw.get("index", i)),
                    start=float(raw.get("start", 0)),
                    end=float(raw.get("end", 0)),
                    text=str(raw.get("text", "")),
                    speaker=str(raw.get("speaker", "")),
                    style=str(raw.get("style", "")),
                )
            )
        except (TypeError, ValueError, ValidationError) as exc:
            raise ParseError(f"item {i}: {exc}", line=i) from exc
    if not cues:
        raise ParseError("no cues found in JSON")
    return Track(name, cues=cues, language=language, created=created)


def parse_json_file(path: str, **kw) -> Track:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise ParseError(f"cannot read file: {exc}") from exc
    return parse_json_text(text, **kw)


def track_to_json(track: Track, *, indent: int | None = 2) -> str:
    return json.dumps(track.to_dict(), indent=indent, ensure_ascii=False, allow_nan=False)
