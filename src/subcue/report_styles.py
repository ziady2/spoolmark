"""Style usage analysis report.

Analyses the distribution and usage patterns of subtitle styles
across cues including transition frequency and per-style timing.
"""

from __future__ import annotations

from collections import Counter
from typing import List

from .cue import Cue
from .math_utils import mean, round_to
from .timing import format_timecode
from .track import Track


def style_usage(track: Track) -> List[dict]:
    """Count cues per style and compute timing statistics.

    Keys
    ----
    style : str
        Style identifier (empty string for unstyled cues).
    cue_count : int
        Number of cues using this style.
    pct_cues : float
        Percentage of total cues.
    total_duration : float
        Combined duration of cues with this style.
    pct_duration : float
        Percentage of total speaking time.
    avg_duration : float
        Mean cue duration for this style.
    avg_chars : float
        Mean character count per cue.
    avg_cps : float
        Mean characters per second.
    """
    groups: dict[str, List[Cue]] = {}
    for cue in track.cues:
        groups.setdefault(cue.style, []).append(cue)
    total_cues = len(track.cues) or 1
    total_dur = sum(c.duration for c in track.cues) or 1.0
    result: List[dict] = []
    for style in sorted(groups):
        cues = groups[style]
        dur = sum(c.duration for c in cues)
        chars = [float(c.char_count) for c in cues]
        cps_vals = [c.cps for c in cues if c.duration > 0]
        result.append(
            {
                "style": style,
                "cue_count": len(cues),
                "pct_cues": round_to(len(cues) / total_cues * 100),
                "total_duration": round_to(dur),
                "pct_duration": round_to(dur / total_dur * 100),
                "avg_duration": round_to(mean([c.duration for c in cues])),
                "avg_chars": round_to(mean(chars)) if chars else 0.0,
                "avg_cps": round_to(mean(cps_vals)) if cps_vals else 0.0,
            }
        )
    return result


def style_transitions(track: Track) -> List[dict]:
    """Identify points where the style changes between consecutive cues.

    Keys
    ----
    position : int
        0-based position in the sorted cue list.
    from_style : str
        Style of the preceding cue.
    to_style : str
        Style of the following cue.
    from_index : int
        Index of the preceding cue.
    to_index : int
        Index of the following cue.
    timecode : str
        Timecode where the transition occurs.
    gap_seconds : float
        Gap between the two cues in seconds.
    """
    sorted_cues = track.sorted_cues()
    result: List[dict] = []
    for i in range(len(sorted_cues) - 1):
        cur = sorted_cues[i]
        nxt = sorted_cues[i + 1]
        if cur.style != nxt.style:
            result.append(
                {
                    "position": i,
                    "from_style": cur.style,
                    "to_style": nxt.style,
                    "from_index": cur.index,
                    "to_index": nxt.index,
                    "timecode": format_timecode(nxt.start),
                    "gap_seconds": round_to(nxt.start - cur.end, 3),
                }
            )
    return result


def style_summary(track: Track) -> List[dict]:
    """High-level style statistics for the track.

    Keys
    ----
    track_name : str
        Name of the track.
    total_cues : int
        Total cues in the track.
    distinct_styles : int
        Number of unique styles found.
    unstyled_count : int
        Number of cues with an empty style.
    unstyled_pct : float
        Percentage of unstyled cues.
    transition_count : int
        Number of style transitions.
    most_used_style : str
        Style with the highest cue count.
    most_used_count : int
        Cue count for the most-used style.
    """
    counter: Counter[str] = Counter(c.style for c in track.cues)
    transitions = style_transitions(track)
    unstyled = counter.get("", 0)
    total = len(track.cues) or 1
    most_style, most_count = counter.most_common(1)[0] if counter else ("", 0)
    return [
        {
            "track_name": track.name,
            "total_cues": len(track.cues),
            "distinct_styles": len(counter),
            "unstyled_count": unstyled,
            "unstyled_pct": round_to(unstyled / total * 100),
            "transition_count": len(transitions),
            "most_used_style": most_style,
            "most_used_count": most_count,
        }
    ]
