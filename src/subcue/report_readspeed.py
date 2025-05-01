"""Reading speed conformance report.

Evaluates each cue against configurable CPS and WPS thresholds to
determine whether the subtitle can be comfortably read by the viewer.
"""

from __future__ import annotations

from typing import List

from .math_utils import mean, percentile, round_to
from .timing import format_timecode
from .timing import wps as calc_wps
from .track import Track

DEFAULT_MAX_CPS: float = 20.0
DEFAULT_MAX_WPS: float = 3.5
DEFAULT_MIN_DURATION: float = 0.7


def readspeed_check(
    track: Track,
    max_cps: float = DEFAULT_MAX_CPS,
    max_wps: float = DEFAULT_MAX_WPS,
    min_duration: float = DEFAULT_MIN_DURATION,
) -> List[dict]:
    """Check each cue against reading-speed limits.

    Keys
    ----
    index : int
        Cue sequence number.
    start_tc : str
        Start timecode.
    duration : float
        Cue duration in seconds.
    cps : float
        Characters per second.
    wps : float
        Words per second.
    cps_ok : bool
        True when CPS is within *max_cps*.
    wps_ok : bool
        True when WPS is within *max_wps*.
    duration_ok : bool
        True when duration meets *min_duration*.
    pass_all : bool
        True when all checks pass.
    text_preview : str
        First 40 characters of the cue text.
    """
    result: List[dict] = []
    for cue in track.sorted_cues():
        c = cue.cps
        w = calc_wps(cue.plain_text, cue.duration)
        c_ok = c <= max_cps
        w_ok = w <= max_wps
        d_ok = cue.duration >= min_duration
        result.append(
            {
                "index": cue.index,
                "start_tc": format_timecode(cue.start),
                "duration": cue.duration,
                "cps": c,
                "wps": round_to(w),
                "cps_ok": c_ok,
                "wps_ok": w_ok,
                "duration_ok": d_ok,
                "pass_all": c_ok and w_ok and d_ok,
                "text_preview": cue.plain_text[:40],
            }
        )
    return result


def readspeed_summary(
    track: Track,
    max_cps: float = DEFAULT_MAX_CPS,
    max_wps: float = DEFAULT_MAX_WPS,
    min_duration: float = DEFAULT_MIN_DURATION,
) -> List[dict]:
    """Aggregate reading-speed statistics.

    Keys
    ----
    track_name : str
        Name of the track.
    cue_count : int
        Total cues analysed.
    pass_count : int
        Cues passing all checks.
    fail_count : int
        Cues failing at least one check.
    pass_rate : float
        Percentage of cues passing.
    cps_fail_count : int
        Cues exceeding CPS limit.
    wps_fail_count : int
        Cues exceeding WPS limit.
    duration_fail_count : int
        Cues below minimum duration.
    avg_cps : float
        Mean CPS across all cues.
    avg_wps : float
        Mean WPS across all cues.
    p95_cps : float
        95th percentile CPS.
    """
    if not track.cues:
        return [
            {
                "track_name": track.name,
                "cue_count": 0,
                "pass_count": 0,
                "fail_count": 0,
                "pass_rate": 0.0,
                "cps_fail_count": 0,
                "wps_fail_count": 0,
                "duration_fail_count": 0,
                "avg_cps": 0.0,
                "avg_wps": 0.0,
                "p95_cps": 0.0,
            }
        ]
    cps_vals: List[float] = []
    wps_vals: List[float] = []
    cps_fail = wps_fail = dur_fail = pass_n = 0
    for cue in track.cues:
        c = cue.cps
        w = calc_wps(cue.plain_text, cue.duration)
        cps_vals.append(c)
        wps_vals.append(w)
        c_ok = c <= max_cps
        w_ok = w <= max_wps
        d_ok = cue.duration >= min_duration
        if not c_ok:
            cps_fail += 1
        if not w_ok:
            wps_fail += 1
        if not d_ok:
            dur_fail += 1
        if c_ok and w_ok and d_ok:
            pass_n += 1
    total = len(track.cues)
    return [
        {
            "track_name": track.name,
            "cue_count": total,
            "pass_count": pass_n,
            "fail_count": total - pass_n,
            "pass_rate": round_to(pass_n / total * 100),
            "cps_fail_count": cps_fail,
            "wps_fail_count": wps_fail,
            "duration_fail_count": dur_fail,
            "avg_cps": round_to(mean(cps_vals)),
            "avg_wps": round_to(mean(wps_vals)),
            "p95_cps": round_to(percentile(cps_vals, 95)),
        }
    ]
