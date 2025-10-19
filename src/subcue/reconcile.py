"""Track reconciliation and diffing utilities."""

from __future__ import annotations

import math
from typing import Any, Sequence

from .cue import Cue
from .track import Track


def field_diff(
    cue_a: Cue,
    cue_b: Cue,
    *,
    fields: Sequence[str] = ("text", "start", "end", "speaker"),
) -> dict[str, tuple[Any, Any]]:
    """Compare two cues field-by-field and return a dict of differences.

    Only fields with differing values are included.

    Parameters
    ----------
    cue_a:
        First cue.
    cue_b:
        Second cue.
    fields:
        Attribute names to compare.
    """
    diffs: dict[str, tuple[Any, Any]] = {}
    for f in fields:
        va = getattr(cue_a, f, None)
        vb = getattr(cue_b, f, None)
        if va != vb:
            diffs[f] = (va, vb)
    return diffs


def diff_tracks(
    track_a: Track,
    track_b: Track,
    *,
    fields: Sequence[str] = ("text", "start", "end", "speaker"),
) -> list[dict[str, Any]]:
    """Produce a diff between two tracks.

    Cues are paired by index.  The result is a list of dicts with
    ``'index'``, ``'status'`` (``'changed'``, ``'added'``, ``'removed'``),
    and ``'diffs'`` (from :func:`field_diff`).
    """
    result: list[dict[str, Any]] = []
    cues_a = {cue.index: cue for cue in track_a.cues}
    cues_b = {cue.index: cue for cue in track_b.cues}
    for index in sorted(cues_a.keys() | cues_b.keys()):
        a = cues_a.get(index)
        b = cues_b.get(index)
        if a is None and b is not None:
            result.append({"index": index, "status": "added", "diffs": {}})
        elif a is not None and b is None:
            result.append({"index": index, "status": "removed", "diffs": {}})
        elif a is not None and b is not None:
            diffs = field_diff(a, b, fields=fields)
            if diffs:
                result.append({"index": index, "status": "changed", "diffs": diffs})
    return result


def merge_tracks_by_time(
    track_a: Track,
    track_b: Track,
    *,
    tolerance: float = 0.1,
    prefer: str = "a",
) -> Track:
    """Merge two tracks by matching cues with overlapping timecodes.

    When cues from both tracks overlap within *tolerance* seconds,
    the cue from the preferred track (*prefer*) is kept.

    Parameters
    ----------
    track_a:
        First track.
    track_b:
        Second track.
    tolerance:
        Maximum start-time difference (seconds) to consider a match.
    prefer:
        ``'a'`` or ``'b'`` \u2013 which track's cue wins on conflict.
    """
    _validate_merge_options(tolerance, prefer)
    used_b: set[int] = set()
    merged: list[Cue] = []
    for ca in track_a.cues:
        candidates = [
            (j, cb)
            for j, cb in enumerate(track_b.cues)
            if j not in used_b and _ranges_match(ca, cb, tolerance)
        ]
        if not candidates:
            merged.append(ca.copy())
            continue
        j, cb = min(
            candidates,
            key=lambda item: (
                abs(ca.start - item[1].start),
                abs(ca.end - item[1].end),
                item[0],
            ),
        )
        merged.append(ca.copy() if prefer == "a" else cb.copy())
        used_b.add(j)
    for j, cb in enumerate(track_b.cues):
        if j not in used_b:
            merged.append(cb.copy())
    merged.sort(key=lambda c: c.start)
    reindexed = [
        Cue(
            i,
            cue.start,
            cue.end,
            cue.text,
            speaker=cue.speaker,
            style=cue.style,
        )
        for i, cue in enumerate(merged, 1)
    ]
    return Track(
        track_a.name,
        cues=reindexed,
        language=track_a.language,
        created=track_a.created,
    )


def conflict_rows(
    track_a: Track,
    track_b: Track,
    *,
    tolerance: float = 0.1,
) -> list[dict[str, Any]]:
    """Return rows where cues from both tracks conflict.

    A conflict occurs when two cues overlap in time but differ in text.

    Parameters
    ----------
    track_a:
        First track.
    track_b:
        Second track.
    tolerance:
        Maximum start-time difference to consider a potential match.
    """
    _validate_tolerance(tolerance)
    conflicts: list[dict[str, Any]] = []
    for ca in track_a.cues:
        for cb in track_b.cues:
            if _ranges_match(ca, cb, tolerance) and ca.text != cb.text:
                conflicts.append(
                    {
                        "start": ca.start,
                        "text_a": ca.text,
                        "text_b": cb.text,
                        "time_diff": abs(ca.start - cb.start),
                    }
                )
    return conflicts


def _ranges_match(cue_a: Cue, cue_b: Cue, tolerance: float) -> bool:
    """Return whether two cue intervals overlap or are within *tolerance*."""
    return cue_a.start <= cue_b.end + tolerance and cue_b.start <= cue_a.end + tolerance


def _validate_tolerance(tolerance: float) -> None:
    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not math.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("tolerance must be a finite non-negative number")


def _validate_merge_options(tolerance: float, prefer: str) -> None:
    _validate_tolerance(tolerance)
    if prefer not in {"a", "b"}:
        raise ValueError("prefer must be 'a' or 'b'")
