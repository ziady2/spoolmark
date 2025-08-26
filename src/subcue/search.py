"""Text search utilities for cue content."""

from __future__ import annotations

import re
from typing import Any, Sequence

from .cue import Cue
from .track import Track


def search_cues(
    cues: Sequence[Cue],
    query: str,
    *,
    case_sensitive: bool = False,
) -> list[Cue]:
    """Return cues whose text contains *query*.

    Parameters
    ----------
    cues:
        Sequence of cues to search.
    query:
        Plain text to look for.
    case_sensitive:
        Whether to do a case-sensitive match.
    """
    if not case_sensitive:
        q = query.lower()
        return [c for c in cues if q in c.text.lower()]
    return [c for c in cues if query in c.text]


def search_by_speaker(
    cues: Sequence[Cue],
    speaker: str,
    *,
    exact: bool = True,
) -> list[Cue]:
    """Return cues matching *speaker*.

    Parameters
    ----------
    speaker:
        Speaker name to match.
    exact:
        If ``True``, match the full name; otherwise match substring.
    """
    if exact:
        return [c for c in cues if c.speaker == speaker]
    s_lower = speaker.lower()
    return [c for c in cues if c.speaker and s_lower in c.speaker.lower()]


def regex_search(
    cues: Sequence[Cue],
    pattern: str,
    *,
    flags: int = 0,
) -> list[dict[str, Any]]:
    """Search cue text with a regular expression.

    Returns a list of dicts with ``'cue'`` and ``'matches'`` keys.

    Parameters
    ----------
    pattern:
        Regular expression pattern.
    flags:
        Regex flags (e.g. ``re.IGNORECASE``).
    """
    compiled = re.compile(pattern, flags)
    results: list[dict[str, Any]] = []
    for cue in cues:
        matches = compiled.findall(cue.text)
        if matches:
            results.append({"cue": cue, "matches": matches})
    return results


def highlight_matches(
    text: str,
    query: str,
    *,
    before: str = ">>",
    after: str = "<<",
    case_sensitive: bool = False,
) -> str:
    """Return *text* with all occurrences of *query* wrapped in markers.

    Parameters
    ----------
    text:
        Source string.
    query:
        Substring to highlight.
    before:
        Marker inserted before each match.
    after:
        Marker inserted after each match.
    """
    if not query:
        return text
    escaped = re.escape(query)
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = re.compile(f"({escaped})", flags)
    return compiled.sub(lambda match: before + match.group(1) + after, text)


def search_track(
    track: Track,
    query: str,
    *,
    case_sensitive: bool = False,
) -> list[Cue]:
    """Convenience wrapper to search cues within a *Track*."""
    return search_cues(track.cues, query, case_sensitive=case_sensitive)
