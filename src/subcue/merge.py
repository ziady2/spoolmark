"""Track merging utilities."""

from __future__ import annotations

import math
from typing import Sequence

from .cue import Cue
from .track import Track


def _reindex(cues: list[Cue]) -> list[Cue]:
    """Return copies of *cues* with sequential 1-based indices."""
    result: list[Cue] = []
    for i, c in enumerate(cues, 1):
        new = c.copy()
        object.__setattr__(new, "index", i)
        result.append(new)
    return result


def merge_tracks(
    tracks: Sequence[Track],
    *,
    name: str = "merged",
) -> Track:
    """Merge multiple tracks into one, sorted by cue start time.

    Parameters
    ----------
    tracks:
        Tracks to merge.
    name:
        Name for the resulting track.
    """
    all_cues: list[Cue] = []
    for t in tracks:
        all_cues.extend(c.copy() for c in t.cues)
    all_cues.sort(key=lambda c: (c.start, c.end))
    reindexed = _reindex(all_cues)
    if not tracks:
        return Track(name=name, cues=[])
    return Track(
        name,
        cues=reindexed,
        language=tracks[0].language,
        created=tracks[0].created,
    )


def interleave_tracks(
    track_a: Track,
    track_b: Track,
    *,
    name: str = "interleaved",
) -> Track:
    """Interleave cues from two tracks by their start times.

    Cues are taken alternately from *track_a* and *track_b*
    in chronological order.
    """
    combined: list[tuple[float, str, Cue]] = []
    for c in track_a.cues:
        combined.append((c.start, "a", c))
    for c in track_b.cues:
        combined.append((c.start, "b", c))
    combined.sort(key=lambda x: (x[0], x[1]))
    merged = [item[2].copy() for item in combined]
    reindexed = _reindex(merged)
    return Track(
        name,
        cues=reindexed,
        language=track_a.language,
        created=track_a.created,
    )


def concatenate_tracks(
    tracks: Sequence[Track],
    *,
    name: str = "concatenated",
    gap: float = 0.0,
) -> Track:
    """Concatenate tracks end-to-end with an optional *gap* between them.

    Each subsequent track's cues are time-shifted so that they follow
    the previous track's last cue.

    Parameters
    ----------
    tracks:
        Ordered sequence of tracks.
    name:
        Name for the resulting track.
    gap:
        Seconds of silence inserted between adjacent tracks.
    """
    if (
        isinstance(gap, bool)
        or not isinstance(gap, (int, float))
        or not math.isfinite(gap)
        or gap < 0
    ):
        raise ValueError("gap must be a finite non-negative number")
    all_cues: list[Cue] = []
    output_end: float | None = None
    for t in tracks:
        if not t.cues:
            continue
        ordered = t.sorted_cues()
        offset = 0.0
        if output_end is not None:
            offset = output_end + gap - ordered[0].start
        shifted_cues = [c.shift(offset) for c in ordered]
        all_cues.extend(shifted_cues)
        output_end = max(c.end for c in shifted_cues)
    reindexed = _reindex(all_cues)
    if not tracks:
        return Track(name=name, cues=[])
    return Track(
        name,
        cues=reindexed,
        language=tracks[0].language,
        created=tracks[0].created,
    )
