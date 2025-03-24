"""Standards conformance report for subtitle tracks.

Checks each cue against configurable broadcast and streaming standards:
maximum CPS, maximum characters per line, maximum number of lines,
and minimum/maximum cue duration.
"""

from __future__ import annotations

from typing import List

from .math_utils import round_to
from .timing import format_timecode
from .track import Track

MAX_CPS: float = 20.0
MAX_CHARS_PER_LINE: int = 42
MAX_LINES: int = 2
MIN_DURATION: float = 0.833
MAX_DURATION: float = 7.0


def conformance_check(track: Track) -> List[dict]:
    """Check every cue against conformance rules.

    Keys
    ----
    index : int
        Cue sequence number.
    start_tc : str
        Start timecode.
    cps : float
        Characters per second.
    cps_ok : bool
        True when CPS <= MAX_CPS.
    max_line_len : int
        Length of the longest line in the cue.
    line_len_ok : bool
        True when all lines are within MAX_CHARS_PER_LINE.
    line_count : int
        Number of lines.
    line_count_ok : bool
        True when line count <= MAX_LINES.
    duration : float
        Cue duration in seconds.
    duration_ok : bool
        True when duration is within [MIN_DURATION, MAX_DURATION].
    pass_all : bool
        True when all checks pass.
    violations : List[str]
        List of violated rule names.
    """
    result: List[dict] = []
    for cue in track.sorted_cues():
        lines = cue.text.split("\n")
        max_ll = max((len(line.strip()) for line in lines), default=0)
        lc = len(lines)
        cps_ok = cue.cps <= MAX_CPS
        ll_ok = max_ll <= MAX_CHARS_PER_LINE
        lc_ok = lc <= MAX_LINES
        dur_ok = MIN_DURATION <= cue.duration <= MAX_DURATION
        violations: List[str] = []
        if not cps_ok:
            violations.append("cps")
        if not ll_ok:
            violations.append("line_length")
        if not lc_ok:
            violations.append("line_count")
        if not dur_ok:
            violations.append("duration")
        result.append(
            {
                "index": cue.index,
                "start_tc": format_timecode(cue.start),
                "cps": cue.cps,
                "cps_ok": cps_ok,
                "max_line_len": max_ll,
                "line_len_ok": ll_ok,
                "line_count": lc,
                "line_count_ok": lc_ok,
                "duration": cue.duration,
                "duration_ok": dur_ok,
                "pass_all": not violations,
                "violations": violations,
            }
        )
    return result


def conformance_summary(track: Track) -> List[dict]:
    """Aggregate conformance results for the whole track.

    Keys
    ----
    track_name : str
        Name of the track.
    total_cues : int
        Total cues checked.
    pass_count : int
        Cues passing all rules.
    fail_count : int
        Cues violating at least one rule.
    pass_rate : float
        Percentage of cues that pass.
    cps_violations : int
        Number of CPS violations.
    line_length_violations : int
        Number of line-length violations.
    line_count_violations : int
        Number of line-count violations.
    duration_violations : int
        Number of duration violations.
    most_common_violation : str
        The rule violated most often (empty if none).
    """
    checks = conformance_check(track)
    total = len(checks) or 1
    pass_n = sum(1 for c in checks if c["pass_all"])
    counts = {"cps": 0, "line_length": 0, "line_count": 0, "duration": 0}
    for c in checks:
        for v in c["violations"]:
            counts[v] = counts.get(v, 0) + 1
    most_common = max(counts, key=lambda k: counts[k]) if any(counts.values()) else ""
    if most_common and counts[most_common] == 0:
        most_common = ""
    return [
        {
            "track_name": track.name,
            "total_cues": len(checks),
            "pass_count": pass_n,
            "fail_count": len(checks) - pass_n,
            "pass_rate": round_to(pass_n / total * 100),
            "cps_violations": counts["cps"],
            "line_length_violations": counts["line_length"],
            "line_count_violations": counts["line_count"],
            "duration_violations": counts["duration"],
            "most_common_violation": most_common,
        }
    ]
