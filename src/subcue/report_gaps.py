"""Gap analysis report between consecutive subtitle cues.

Measures the silence gaps between each pair of consecutive cues and
provides per-gap detail, aggregated statistics, and long-gap flagging.
"""

from __future__ import annotations

import math
from typing import List

from .math_utils import mean, median, round_to, stdev
from .timing import format_duration_human, format_timecode
from .timing import gap as calc_gap
from .track import Track

DEFAULT_LONG_GAP_THRESHOLD: float = 5.0


def gap_analysis(track: Track) -> List[dict]:
    """Return gap details between every pair of consecutive cues.

    Keys
    ----
    from_index : int
        Index of the preceding cue.
    to_index : int
        Index of the following cue.
    from_end_tc : str
        End timecode of the preceding cue.
    to_start_tc : str
        Start timecode of the following cue.
    gap_seconds : float
        Gap duration in seconds (negative means overlap).
    gap_human : str
        Human-readable gap duration.
    is_overlap : bool
        True when the gap is negative (cues overlap).
    """
    result: List[dict] = []
    for cur, nxt in track.timeline_pairs():
        g = calc_gap(cur.end, nxt.start)
        result.append(
            {
                "from_index": cur.index,
                "to_index": nxt.index,
                "from_end_tc": format_timecode(cur.end),
                "to_start_tc": format_timecode(nxt.start),
                "gap_seconds": round_to(g, 3),
                "gap_human": format_duration_human(abs(g)),
                "is_overlap": g < 0,
            }
        )
    return result


def gap_summary(track: Track) -> List[dict]:
    """Aggregate gap statistics across all consecutive pairs.

    Keys
    ----
    track_name : str
        Name of the track.
    pair_count : int
        Number of consecutive cue pairs.
    avg_gap : float
        Mean gap in seconds.
    median_gap : float
        Median gap in seconds.
    min_gap : float
        Smallest gap (most negative means worst overlap).
    max_gap : float
        Largest gap in seconds.
    stdev_gap : float
        Standard deviation of gap values.
    negative_count : int
        Number of pairs with negative gaps (overlaps).
    zero_count : int
        Number of pairs with zero gap.
    positive_count : int
        Number of pairs with positive gap.
    """
    pairs = track.timeline_pairs()
    if not pairs:
        return [
            {
                "track_name": track.name,
                "pair_count": 0,
                "avg_gap": 0.0,
                "median_gap": 0.0,
                "min_gap": 0.0,
                "max_gap": 0.0,
                "stdev_gap": 0.0,
                "negative_count": 0,
                "zero_count": 0,
                "positive_count": 0,
            }
        ]
    gaps = [calc_gap(left.end, right.start) for left, right in pairs]
    return [
        {
            "track_name": track.name,
            "pair_count": len(gaps),
            "avg_gap": round_to(mean(gaps), 3),
            "median_gap": round_to(median(gaps), 3),
            "min_gap": round_to(min(gaps), 3),
            "max_gap": round_to(max(gaps), 3),
            "stdev_gap": round_to(stdev(gaps), 3),
            "negative_count": sum(1 for g in gaps if g < 0),
            "zero_count": sum(1 for g in gaps if g == 0.0),
            "positive_count": sum(1 for g in gaps if g > 0),
        }
    ]


def long_gaps(
    track: Track,
    threshold: float = DEFAULT_LONG_GAP_THRESHOLD,
) -> List[dict]:
    """Return gaps that exceed *threshold* seconds.

    Keys
    ----
    from_index : int
        Index of the preceding cue.
    to_index : int
        Index of the following cue.
    gap_seconds : float
        Gap duration in seconds.
    excess : float
        Amount by which the gap exceeds the threshold.
    from_end_tc : str
        End timecode of the preceding cue.
    to_start_tc : str
        Start timecode of the following cue.
    """
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(threshold)
        or threshold < 0
    ):
        raise ValueError("threshold must be a finite non-negative number")
    result: List[dict] = []
    for cur, nxt in track.timeline_pairs():
        g = calc_gap(cur.end, nxt.start)
        if g > threshold:
            result.append(
                {
                    "from_index": cur.index,
                    "to_index": nxt.index,
                    "gap_seconds": round_to(g, 3),
                    "excess": round_to(g - threshold, 3),
                    "from_end_tc": format_timecode(cur.end),
                    "to_start_tc": format_timecode(nxt.start),
                }
            )
    return result
