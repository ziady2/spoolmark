"""Timing statistics report for subtitle tracks.

Provides aggregate and per-cue timing metrics including average,
minimum, maximum, median durations and quartile breakdowns.
"""

from __future__ import annotations

from typing import List

from .math_utils import mean, median, percentile, round_to, stdev
from .timing import format_duration_human, format_timecode
from .track import Track


def timing_summary(track: Track) -> List[dict]:
    """Compute overall timing statistics for the track.

    Returns a single-element list with aggregate timing metrics.

    Keys
    ----
    track_name : str
        Name of the track.
    cue_count : int
        Total number of cues.
    total_duration : float
        Total track duration in seconds.
    total_duration_human : str
        Human-readable total duration.
    avg_duration : float
        Mean cue duration in seconds.
    min_duration : float
        Shortest cue duration in seconds.
    max_duration : float
        Longest cue duration in seconds.
    median_duration : float
        Median cue duration in seconds.
    stdev_duration : float
        Standard deviation of durations.
    p95_duration : float
        95th percentile duration.
    """
    if not track.cues:
        return [
            {
                "track_name": track.name,
                "cue_count": 0,
                "total_duration": 0.0,
                "total_duration_human": "0s",
                "avg_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "median_duration": 0.0,
                "stdev_duration": 0.0,
                "p95_duration": 0.0,
            }
        ]
    durations: List[float] = [c.duration for c in track.cues]
    return [
        {
            "track_name": track.name,
            "cue_count": len(track.cues),
            "total_duration": round_to(track.duration),
            "total_duration_human": format_duration_human(track.duration),
            "avg_duration": round_to(mean(durations)),
            "min_duration": round_to(min(durations)),
            "max_duration": round_to(max(durations)),
            "median_duration": round_to(median(durations)),
            "stdev_duration": round_to(stdev(durations)),
            "p95_duration": round_to(percentile(durations, 95)),
        }
    ]


def timing_per_cue(track: Track) -> List[dict]:
    """Return per-cue timing details with formatted timecodes.

    Keys
    ----
    index : int
        Cue sequence number.
    start : float
        Start time in seconds.
    end : float
        End time in seconds.
    start_tc : str
        Formatted start timecode.
    end_tc : str
        Formatted end timecode.
    duration : float
        Cue duration in seconds.
    pct_of_total : float
        Duration as percentage of total track duration.
    """
    total_dur = track.duration if track.duration > 0 else 1.0
    result: List[dict] = []
    for cue in track.sorted_cues():
        pct = round_to((cue.duration / total_dur) * 100)
        result.append(
            {
                "index": cue.index,
                "start": cue.start,
                "end": cue.end,
                "start_tc": format_timecode(cue.start),
                "end_tc": format_timecode(cue.end),
                "duration": cue.duration,
                "pct_of_total": pct,
            }
        )
    return result


def timing_quartiles(track: Track) -> List[dict]:
    """Break cue durations into quartile ranges.

    Keys
    ----
    quartile : str
        Label such as ``Q1``, ``Q2``, ``Q3``, ``Q4``.
    lower_bound : float
        Lower bound of the quartile in seconds.
    upper_bound : float
        Upper bound of the quartile in seconds.
    count : int
        Number of cues in this quartile.
    pct : float
        Percentage of cues in this quartile.
    """
    if not track.cues:
        return []
    durations = [c.duration for c in track.cues]
    bounds = [
        percentile(durations, 0),
        percentile(durations, 25),
        percentile(durations, 50),
        percentile(durations, 75),
        percentile(durations, 100),
    ]
    labels = ["Q1", "Q2", "Q3", "Q4"]
    result: List[dict] = []
    total = len(durations)
    for i, label in enumerate(labels):
        lo = bounds[i]
        hi = bounds[i + 1]
        if i < 3:
            cnt = sum(1 for d in durations if lo <= d < hi)
        else:
            cnt = sum(1 for d in durations if lo <= d <= hi)
        result.append(
            {
                "quartile": label,
                "lower_bound": round_to(lo),
                "upper_bound": round_to(hi),
                "count": cnt,
                "pct": round_to((cnt / total) * 100) if total else 0.0,
            }
        )
    return result
