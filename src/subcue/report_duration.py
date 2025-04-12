"""Cue duration distribution report.

Distributes cue durations into configurable buckets and surfaces the
shortest and longest cues for review.
"""

from __future__ import annotations

from typing import List

from .cue import Cue
from .math_utils import bucket, mean, round_to
from .timing import format_timecode
from .track import Track

DEFAULT_BOUNDARIES: List[float] = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
BUCKET_LABELS: List[str] = [
    "<1s",
    "1-2s",
    "2-3s",
    "3-5s",
    "5-7s",
    "7-10s",
    ">=10s",
]


def duration_buckets(
    track: Track,
    boundaries: List[float] | None = None,
) -> List[dict]:
    """Distribute cue durations into buckets.

    Keys
    ----
    bucket_label : str
        Human-readable bucket range.
    lower_bound : float
        Inclusive lower bound in seconds (0 for first).
    upper_bound : float | None
        Exclusive upper bound in seconds (None for last).
    count : int
        Number of cues in this bucket.
    pct : float
        Percentage of total cues.
    avg_chars : float
        Average character count of cues in this bucket.
    avg_cps : float
        Average CPS of cues in this bucket.
    """
    bounds = boundaries or DEFAULT_BOUNDARIES
    labels = BUCKET_LABELS if boundaries is None else None
    n_buckets = len(bounds) + 1
    buckets: List[List[Cue]] = [[] for _ in range(n_buckets)]
    for cue in track.cues:
        idx = bucket(cue.duration, bounds)
        buckets[idx].append(cue)
    total = len(track.cues) or 1
    result: List[dict] = []
    for i in range(n_buckets):
        cues_in = buckets[i]
        lo = bounds[i - 1] if i > 0 else 0.0
        hi: float | None = bounds[i] if i < len(bounds) else None
        if labels and i < len(labels):
            lbl = labels[i]
        else:
            lbl = f"{lo}s+" if hi is None else f"{lo}-{hi}s"
        avg_ch = mean([float(c.char_count) for c in cues_in]) if cues_in else 0.0
        avg_cp = mean([c.cps for c in cues_in]) if cues_in else 0.0
        result.append(
            {
                "bucket_label": lbl,
                "lower_bound": lo,
                "upper_bound": hi,
                "count": len(cues_in),
                "pct": round_to(len(cues_in) / total * 100),
                "avg_chars": round_to(avg_ch),
                "avg_cps": round_to(avg_cp),
            }
        )
    return result


def duration_extremes(
    track: Track,
    n: int = 10,
) -> List[dict]:
    """Return the *n* shortest and *n* longest cues.

    Keys
    ----
    category : str
        ``shortest`` or ``longest``.
    rank : int
        1-based rank within the category.
    index : int
        Cue sequence number.
    start_tc : str
        Start timecode.
    duration : float
        Duration in seconds.
    char_count : int
        Character count of the cue.
    text_preview : str
        First 40 characters of the cue text.
    """
    if n <= 0:
        raise ValueError("n must be greater than zero")

    sorted_by_dur = sorted(track.cues, key=lambda c: c.duration)
    result: List[dict] = []
    shortest = sorted_by_dur[:n]
    longest = sorted_by_dur[-n:] if len(sorted_by_dur) > n else sorted_by_dur
    longest = list(reversed(longest))
    for rank, cue in enumerate(shortest, start=1):
        result.append(
            {
                "category": "shortest",
                "rank": rank,
                "index": cue.index,
                "start_tc": format_timecode(cue.start),
                "duration": cue.duration,
                "char_count": cue.char_count,
                "text_preview": cue.plain_text[:40],
            }
        )
    for rank, cue in enumerate(longest, start=1):
        result.append(
            {
                "category": "longest",
                "rank": rank,
                "index": cue.index,
                "start_tc": format_timecode(cue.start),
                "duration": cue.duration,
                "char_count": cue.char_count,
                "text_preview": cue.plain_text[:40],
            }
        )
    return result
