"""Overlapping cue detection report.

Identifies pairs of cues that overlap in time and quantifies the
amount of overlap, providing both detail and summary views.
"""

from __future__ import annotations

from typing import List

from .math_utils import mean, round_to, safe_divide
from .timing import format_duration_human, format_timecode
from .timing import overlap as calc_overlap
from .track import Track


def find_overlaps(track: Track) -> List[dict]:
    """Detect all overlapping cue pairs.

    Keys
    ----
    cue_a_index : int
        Index of the first cue.
    cue_b_index : int
        Index of the second cue.
    cue_a_start_tc : str
        Start timecode of cue A.
    cue_a_end_tc : str
        End timecode of cue A.
    cue_b_start_tc : str
        Start timecode of cue B.
    cue_b_end_tc : str
        End timecode of cue B.
    overlap_seconds : float
        Duration of the overlap in seconds.
    overlap_human : str
        Human-readable overlap duration.
    cue_a_text : str
        First 40 characters of cue A text.
    cue_b_text : str
        First 40 characters of cue B text.
    """
    pairs = track.overlapping_pairs()
    result: List[dict] = []
    for cue_a, cue_b in pairs:
        ov = calc_overlap(cue_a.start, cue_a.end, cue_b.start, cue_b.end)
        result.append(
            {
                "cue_a_index": cue_a.index,
                "cue_b_index": cue_b.index,
                "cue_a_start_tc": format_timecode(cue_a.start),
                "cue_a_end_tc": format_timecode(cue_a.end),
                "cue_b_start_tc": format_timecode(cue_b.start),
                "cue_b_end_tc": format_timecode(cue_b.end),
                "overlap_seconds": round_to(ov),
                "overlap_human": format_duration_human(ov),
                "cue_a_text": cue_a.plain_text[:40],
                "cue_b_text": cue_b.plain_text[:40],
            }
        )
    return result


def overlap_summary(track: Track) -> List[dict]:
    """Aggregate overlap statistics for the track.

    Keys
    ----
    track_name : str
        Name of the track.
    total_cues : int
        Total number of cues in the track.
    overlap_pair_count : int
        Number of overlapping pairs found.
    total_overlap_seconds : float
        Combined overlap duration.
    avg_overlap_seconds : float
        Average overlap duration.
    max_overlap_seconds : float
        Longest single overlap.
    pct_cues_involved : float
        Percentage of cues involved in at least one overlap.
    """
    pairs = track.overlapping_pairs()
    if not pairs:
        return [
            {
                "track_name": track.name,
                "total_cues": len(track.cues),
                "overlap_pair_count": 0,
                "total_overlap_seconds": 0.0,
                "avg_overlap_seconds": 0.0,
                "max_overlap_seconds": 0.0,
                "pct_cues_involved": 0.0,
            }
        ]
    overlaps: List[float] = []
    involved: set[int] = set()
    for cue_a, cue_b in pairs:
        ov = calc_overlap(cue_a.start, cue_a.end, cue_b.start, cue_b.end)
        overlaps.append(ov)
        involved.add(cue_a.index)
        involved.add(cue_b.index)
    total_cues = len(track.cues) if track.cues else 1
    return [
        {
            "track_name": track.name,
            "total_cues": len(track.cues),
            "overlap_pair_count": len(pairs),
            "total_overlap_seconds": round_to(sum(overlaps)),
            "avg_overlap_seconds": round_to(mean(overlaps)),
            "max_overlap_seconds": round_to(max(overlaps)),
            "pct_cues_involved": round_to(safe_divide(len(involved) * 100, total_cues)),
        }
    ]
