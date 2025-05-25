"""Sync validation report for subtitle tracks.

Detects timing anomalies such as overlaps, negative gaps, excessively
short cues, and out-of-order cues that indicate synchronisation problems.
"""

from __future__ import annotations

from typing import List

from .math_utils import round_to
from .timing import (
    format_timecode,
)
from .timing import (
    gap as calc_gap,
)
from .timing import (
    overlap as calc_overlap,
)
from .track import Track

SEVERITY_ERROR: str = "error"
SEVERITY_WARN: str = "warning"
SEVERITY_INFO: str = "info"

MIN_CUE_DURATION: float = 0.3
MIN_GAP: float = 0.04


def sync_issues(track: Track) -> List[dict]:
    """Detect sync issues in the track.

    Checks for overlapping cues, gaps smaller than *MIN_GAP*, cues
    shorter than *MIN_CUE_DURATION*, and out-of-order cues.

    Keys
    ----
    issue_type : str
        One of ``overlap``, ``short_gap``, ``short_cue``, ``order``.
    severity : str
        ``error``, ``warning``, or ``info``.
    cue_index : int
        Primary cue involved.
    other_index : int | None
        Second cue involved (if applicable).
    timecode : str
        Timecode where the issue occurs.
    detail : str
        Human-readable description of the issue.
    value : float
        Measured value (overlap duration, gap, cue duration, etc.).
    """
    sorted_cues = track.sorted_cues()
    result: List[dict] = []
    for cue in sorted_cues:
        if cue.duration < MIN_CUE_DURATION:
            result.append(
                {
                    "issue_type": "short_cue",
                    "severity": SEVERITY_WARN,
                    "cue_index": cue.index,
                    "other_index": None,
                    "timecode": format_timecode(cue.start),
                    "detail": f"Cue duration {cue.duration:.3f}s < {MIN_CUE_DURATION}s",
                    "value": cue.duration,
                }
            )
    for cur, nxt in track.overlapping_pairs():
        ov = calc_overlap(cur.start, cur.end, nxt.start, nxt.end)
        result.append(
            {
                "issue_type": "overlap",
                "severity": SEVERITY_ERROR,
                "cue_index": cur.index,
                "other_index": nxt.index,
                "timecode": format_timecode(nxt.start),
                "detail": f"Overlap of {ov:.3f}s between cues",
                "value": ov,
            }
        )
    for cur, nxt in track.timeline_pairs():
        g = calc_gap(cur.end, nxt.start)
        if 0 < g < MIN_GAP:
            result.append(
                {
                    "issue_type": "short_gap",
                    "severity": SEVERITY_WARN,
                    "cue_index": cur.index,
                    "other_index": nxt.index,
                    "timecode": format_timecode(cur.end),
                    "detail": f"Gap {g:.3f}s < {MIN_GAP}s",
                    "value": g,
                }
            )
    raw_cues = track.cues
    for i in range(len(raw_cues) - 1):
        if raw_cues[i].start > raw_cues[i + 1].start:
            result.append(
                {
                    "issue_type": "order",
                    "severity": SEVERITY_ERROR,
                    "cue_index": raw_cues[i].index,
                    "other_index": raw_cues[i + 1].index,
                    "timecode": format_timecode(raw_cues[i].start),
                    "detail": "Cue is out of chronological order",
                    "value": raw_cues[i].start - raw_cues[i + 1].start,
                }
            )
    return result


def sync_summary(track: Track) -> List[dict]:
    """Aggregate sync-issue statistics.

    Keys
    ----
    track_name : str
        Name of the track.
    total_cues : int
        Total number of cues.
    total_issues : int
        Total number of issues found.
    error_count : int
        Number of errors.
    warning_count : int
        Number of warnings.
    overlap_count : int
        Number of overlapping pairs.
    short_gap_count : int
        Number of short gaps detected.
    short_cue_count : int
        Number of very short cues.
    order_count : int
        Number of out-of-order cues.
    health_score : float
        Score from 0 to 100 (higher is better).
    """
    issues = sync_issues(track)
    counts: dict[str, int] = {
        "overlap": 0,
        "short_gap": 0,
        "short_cue": 0,
        "order": 0,
    }
    errors = warnings = 0
    for iss in issues:
        counts[iss["issue_type"]] = counts.get(iss["issue_type"], 0) + 1
        if iss["severity"] == SEVERITY_ERROR:
            errors += 1
        elif iss["severity"] == SEVERITY_WARN:
            warnings += 1
    total_cues = len(track.cues) or 1
    penalty = (errors * 2 + warnings) / total_cues * 100
    score = max(0.0, 100.0 - penalty)
    return [
        {
            "track_name": track.name,
            "total_cues": len(track.cues),
            "total_issues": len(issues),
            "error_count": errors,
            "warning_count": warnings,
            "overlap_count": counts["overlap"],
            "short_gap_count": counts["short_gap"],
            "short_cue_count": counts["short_cue"],
            "order_count": counts["order"],
            "health_score": round_to(score),
        }
    ]
