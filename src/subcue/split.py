"""Track splitting utilities."""

from __future__ import annotations

import math

from .cue import Cue
from .track import Track


def _make_track(name: str, cues: list[Cue], source: Track) -> Track:
    """Helper to build a track from a cue list."""
    return Track(
        name,
        cues=[c.copy() for c in cues],
        language=source.language,
        created=source.created,
    )


def split_by_speaker(track: Track) -> dict[str, Track]:
    """Split a track into one track per speaker.

    Returns a dict mapping speaker names to tracks.
    Cues with no speaker are grouped under ``'(unknown)'``.
    """
    groups: dict[str, list[Cue]] = {}
    for c in track.cues:
        key = c.speaker or "(unknown)"
        groups.setdefault(key, []).append(c)
    return {spk: _make_track(spk, cues, track) for spk, cues in groups.items()}


def split_by_time(
    track: Track,
    interval: float,
) -> list[Track]:
    """Split *track* into segments of *interval* seconds.

    Parameters
    ----------
    track:
        The track to split.
    interval:
        Segment duration in seconds.
    """
    if isinstance(interval, bool) or not isinstance(interval, (int, float)):
        raise ValueError("interval must be a finite positive number")
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("interval must be a finite positive number")
    groups: dict[int, list[Cue]] = {}
    for cue in sorted(track.cues, key=lambda c: c.start):
        window = math.floor(cue.start / interval)
        groups.setdefault(window, []).append(cue)
    result: list[Track] = []
    for idx, window in enumerate(sorted(groups)):
        name = f"{track.name or 'segment'}_{idx + 1}"
        result.append(_make_track(name, groups[window], track))
    return result


def split_at_gaps(
    track: Track,
    min_gap: float = 2.0,
) -> list[Track]:
    """Split *track* wherever a gap between cues exceeds *min_gap* seconds.

    Parameters
    ----------
    track:
        The track to split.
    min_gap:
        Minimum silence duration (in seconds) to trigger a split.
    """
    if isinstance(min_gap, bool) or not isinstance(min_gap, (int, float)):
        raise ValueError("min_gap must be a finite non-negative number")
    if not math.isfinite(min_gap) or min_gap < 0:
        raise ValueError("min_gap must be a finite non-negative number")
    cues = sorted(track.cues, key=lambda c: c.start)
    if not cues:
        return []
    segments: list[list[Cue]] = [[cues[0]]]
    for frontier, cur in track.timeline_pairs():
        if cur.start - frontier.end >= min_gap:
            segments.append([])
        segments[-1].append(cur)
    return [
        _make_track(f"{track.name or 'part'}_{i + 1}", seg, track) for i, seg in enumerate(segments)
    ]


def split_by_style(track: Track) -> dict[str, Track]:
    """Split a track into one track per unique cue style.

    Returns a dict mapping style strings to tracks.
    Cues with no style are grouped under ``'(default)'``.
    """
    groups: dict[str, list[Cue]] = {}
    for c in track.cues:
        key = c.style or "(default)"
        groups.setdefault(key, []).append(c)
    return {style: _make_track(style, cues, track) for style, cues in groups.items()}
