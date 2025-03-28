"""Characters-per-second analysis report.

Analyses the reading speed of each cue measured in characters per
second (CPS) and flags cues that exceed recommended thresholds.
"""

from __future__ import annotations

from typing import List

from .math_utils import mean, median, percentile, round_to, stdev
from .timing import format_timecode
from .track import Track

DEFAULT_CPS_WARN: float = 15.0
DEFAULT_CPS_ERROR: float = 25.0


def cps_per_cue(track: Track) -> List[dict]:
    """Return CPS value for every cue in the track.

    Keys
    ----
    index : int
        Cue sequence number.
    start_tc : str
        Start timecode.
    text_preview : str
        First 40 characters of the cue text.
    char_count : int
        Number of characters in the plain text.
    duration : float
        Cue duration in seconds.
    cps : float
        Characters per second.
    rating : str
        ``ok``, ``warn``, or ``error`` based on thresholds.
    """
    result: List[dict] = []
    for cue in track.sorted_cues():
        cps_val = cue.cps
        if cps_val > DEFAULT_CPS_ERROR:
            rating = "error"
        elif cps_val > DEFAULT_CPS_WARN:
            rating = "warn"
        else:
            rating = "ok"
        result.append(
            {
                "index": cue.index,
                "start_tc": format_timecode(cue.start),
                "text_preview": cue.plain_text[:40],
                "char_count": cue.char_count,
                "duration": cue.duration,
                "cps": cps_val,
                "rating": rating,
            }
        )
    return result


def cps_summary(track: Track) -> List[dict]:
    """Aggregate CPS statistics for the entire track.

    Keys
    ----
    track_name : str
        Name of the track.
    cue_count : int
        Total cues analysed.
    avg_cps : float
        Mean CPS across all cues.
    median_cps : float
        Median CPS.
    min_cps : float
        Lowest CPS value.
    max_cps : float
        Highest CPS value.
    stdev_cps : float
        Standard deviation of CPS values.
    p90_cps : float
        90th percentile CPS.
    warn_count : int
        Cues above the warning threshold.
    error_count : int
        Cues above the error threshold.
    """
    if not track.cues:
        return [
            {
                "track_name": track.name,
                "cue_count": 0,
                "avg_cps": 0.0,
                "median_cps": 0.0,
                "min_cps": 0.0,
                "max_cps": 0.0,
                "stdev_cps": 0.0,
                "p90_cps": 0.0,
                "warn_count": 0,
                "error_count": 0,
            }
        ]
    values: List[float] = [c.cps for c in track.cues]
    return [
        {
            "track_name": track.name,
            "cue_count": len(values),
            "avg_cps": round_to(mean(values)),
            "median_cps": round_to(median(values)),
            "min_cps": round_to(min(values)),
            "max_cps": round_to(max(values)),
            "stdev_cps": round_to(stdev(values)),
            "p90_cps": round_to(percentile(values, 90)),
            "warn_count": sum(1 for v in values if v > DEFAULT_CPS_WARN),
            "error_count": sum(1 for v in values if v > DEFAULT_CPS_ERROR),
        }
    ]


def cps_outliers(
    track: Track,
    threshold: float = DEFAULT_CPS_ERROR,
) -> List[dict]:
    """Return cues whose CPS exceeds *threshold*.

    Keys
    ----
    index : int
        Cue sequence number.
    start_tc : str
        Start timecode.
    cps : float
        Characters per second.
    excess : float
        Amount by which CPS exceeds the threshold.
    text_preview : str
        First 50 characters of the cue text.
    """
    result: List[dict] = []
    for cue in track.sorted_cues():
        if cue.cps > threshold:
            result.append(
                {
                    "index": cue.index,
                    "start_tc": format_timecode(cue.start),
                    "cps": cue.cps,
                    "excess": round_to(cue.cps - threshold),
                    "text_preview": cue.plain_text[:50],
                }
            )
    return result
