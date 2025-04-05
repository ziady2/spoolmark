"""Subtitle density over time intervals report.

Measures how dense subtitles are in fixed time intervals across
the track, useful for identifying overloaded or sparse segments.
"""

from __future__ import annotations

import math
from typing import List

from .math_utils import mean, round_to, safe_divide, stdev
from .timing import format_timecode
from .track import Track

DEFAULT_INTERVAL: float = 30.0


def density_over_time(
    track: Track,
    interval: float = DEFAULT_INTERVAL,
) -> List[dict]:
    """Compute subtitle density per time interval.

    Keys
    ----
    interval_index : int
        0-based interval number.
    start_time : float
        Start of the interval in seconds.
    end_time : float
        End of the interval in seconds.
    start_tc : str
        Formatted start timecode.
    end_tc : str
        Formatted end timecode.
    cue_count : int
        Number of cues active during this interval.
    total_chars : int
        Total characters displayed in this interval.
    total_words : int
        Total words displayed in this interval.
    active_seconds : float
        Seconds of the interval with active subtitles.
    density_pct : float
        Percentage of interval covered by subtitles.
    """
    if (
        isinstance(interval, bool)
        or not isinstance(interval, (int, float))
        or not math.isfinite(interval)
        or interval <= 0
    ):
        raise ValueError("interval must be a finite number greater than zero")
    if not track.cues:
        return []
    sorted_cues = track.sorted_cues()
    track_start = sorted_cues[0].start
    track_end = max(cue.end for cue in sorted_cues)
    n_intervals = max(1, math.ceil((track_end - track_start) / interval))
    result: List[dict] = []
    for idx in range(n_intervals):
        win_start = track_start + idx * interval
        win_end = min(win_start + interval, track_end)
        win_dur = win_end - win_start
        active_ranges: list[tuple[float, float]] = []
        chars = 0
        words = 0
        count = 0
        for cue in sorted_cues:
            if cue.end <= win_start or cue.start >= win_end:
                continue
            count += 1
            chars += cue.char_count
            words += cue.word_count
            cs = max(cue.start, win_start)
            ce = min(cue.end, win_end)
            active_ranges.append((cs, ce))
        active = _union_duration(active_ranges)
        result.append(
            {
                "interval_index": idx,
                "start_time": round_to(win_start, 3),
                "end_time": round_to(win_end, 3),
                "start_tc": format_timecode(win_start),
                "end_tc": format_timecode(win_end),
                "cue_count": count,
                "total_chars": chars,
                "total_words": words,
                "active_seconds": round_to(active, 3),
                "density_pct": round_to(safe_divide(active, win_dur) * 100),
            }
        )
    return result


def _union_duration(ranges: list[tuple[float, float]]) -> float:
    """Return the covered duration of possibly overlapping ranges."""
    if not ranges:
        return 0.0
    ordered = sorted(ranges)
    start, end = ordered[0]
    total = 0.0
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + end - start


def density_summary(track: Track, interval: float = DEFAULT_INTERVAL) -> List[dict]:
    """Aggregate density statistics across all intervals.

    Keys
    ----
    track_name : str
        Name of the track.
    interval_seconds : float
        Interval length used for analysis.
    total_intervals : int
        Number of intervals analysed.
    avg_cues_per_interval : float
        Mean cue count per interval.
    max_cues_in_interval : int
        Highest cue count in a single interval.
    min_density_pct : float
        Lowest density percentage.
    max_density_pct : float
        Highest density percentage.
    avg_density_pct : float
        Mean density percentage.
    stdev_density_pct : float
        Standard deviation of density percentages.
    sparse_intervals : int
        Intervals with density below 20%.
    dense_intervals : int
        Intervals with density above 80%.
    """
    intervals = density_over_time(track, interval)
    if not intervals:
        return [
            {
                "track_name": track.name,
                "interval_seconds": interval,
                "total_intervals": 0,
                "avg_cues_per_interval": 0.0,
                "max_cues_in_interval": 0,
                "min_density_pct": 0.0,
                "max_density_pct": 0.0,
                "avg_density_pct": 0.0,
                "stdev_density_pct": 0.0,
                "sparse_intervals": 0,
                "dense_intervals": 0,
            }
        ]
    counts = [float(d["cue_count"]) for d in intervals]
    densities = [d["density_pct"] for d in intervals]
    return [
        {
            "track_name": track.name,
            "interval_seconds": interval,
            "total_intervals": len(intervals),
            "avg_cues_per_interval": round_to(mean(counts)),
            "max_cues_in_interval": int(max(counts)),
            "min_density_pct": round_to(min(densities)),
            "max_density_pct": round_to(max(densities)),
            "avg_density_pct": round_to(mean(densities)),
            "stdev_density_pct": round_to(stdev(densities)),
            "sparse_intervals": sum(1 for d in densities if d < 20.0),
            "dense_intervals": sum(1 for d in densities if d > 80.0),
        }
    ]
