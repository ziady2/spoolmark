"""JSON export utilities for tracks and reports."""

from __future__ import annotations

import json
from typing import Any, Sequence

from .cue import Cue
from .track import Track


def _cue_dict(cue: Cue) -> dict[str, Any]:
    """Convert a *Cue* to a plain dict suitable for JSON serialisation."""
    return {
        "index": cue.index,
        "start": cue.start,
        "end": cue.end,
        "text": cue.text,
        "speaker": cue.speaker,
        "style": cue.style,
        "duration": cue.duration,
        "char_count": cue.char_count,
        "word_count": cue.word_count,
    }


def _track_dict(track: Track) -> dict[str, Any]:
    """Convert a *Track* to a serialisable dict."""
    return {
        "name": track.name,
        "language": track.language,
        "created": track.created,
        "duration": track.duration,
        "cue_count": len(track.cues),
        "cues": [_cue_dict(c) for c in track.cues],
    }


def export_track_json(
    track: Track,
    *,
    indent: int | None = 2,
    ensure_ascii: bool = False,
) -> str:
    """Serialise a *Track* as a pretty-printed JSON string.

    Parameters
    ----------
    track:
        The track to export.
    indent:
        JSON indentation level; ``None`` for compact output.
    ensure_ascii:
        If ``True`` non-ASCII characters are escaped.
    """
    data = _track_dict(track)
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, allow_nan=False)


def export_report_json(
    report: dict[str, Any],
    *,
    indent: int | None = 2,
) -> str:
    """Serialise a generic report dict as JSON.

    The *report* dict should contain only JSON-compatible types.
    """
    return json.dumps(report, indent=indent, default=str, allow_nan=False)


def minified_json(data: Any) -> str:
    """Return *data* as compact single-line JSON.

    Uses *separators* to strip unnecessary whitespace.
    """
    return json.dumps(data, separators=(",", ":"), default=str, allow_nan=False)


def export_cues_json(
    cues: Sequence[Cue],
    *,
    indent: int | None = 2,
) -> str:
    """Serialise a sequence of cues as a JSON array string.

    Parameters
    ----------
    cues:
        Cue objects to export.
    indent:
        JSON indentation level.
    """
    payload = [_cue_dict(c) for c in cues]
    return json.dumps(payload, indent=indent, default=str, allow_nan=False)
