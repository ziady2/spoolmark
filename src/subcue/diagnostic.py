"""High-level subtitle diagnostics and severity-weighted health scoring.

The functions return stable, table-friendly dictionaries and never modify the
supplied :class:`~subcue.track.Track`.
"""

from __future__ import annotations

import math
from typing import Any, List

from .cue import Cue
from .text_utils import strip_all_tags
from .timing import format_timecode
from .track import Track

SEVERITY_ERROR: str = "error"
SEVERITY_WARNING: str = "warning"
SEVERITY_INFO: str = "info"

DEFAULT_MAX_CPS: float = 20.0
DEFAULT_MIN_DURATION: float = 0.7
DEFAULT_MAX_DURATION: float = 7.0
DEFAULT_MAX_LINES: int = 2
DEFAULT_MAX_CHARS_PER_LINE: int = 42
DEFAULT_MIN_GAP: float = 0.04

# An error costs three times as much as a warning.  The total is capped at 100.
SEVERITY_PENALTIES: dict[str, float] = {
    SEVERITY_ERROR: 15.0,
    SEVERITY_WARNING: 5.0,
    SEVERITY_INFO: 1.0,
}

_SEVERITY_ORDER: dict[str, int] = {
    SEVERITY_ERROR: 0,
    SEVERITY_WARNING: 1,
    SEVERITY_INFO: 2,
}


def _issue(
    issue_type: str,
    severity: str,
    cue_index: int | None,
    message: str,
    *,
    other_index: int | None = None,
    timecode: str = "",
    value: int | float | None = None,
    threshold: int | float | None = None,
) -> dict[str, Any]:
    """Build a diagnostic row with a consistent set of keys."""
    return {
        "issue_type": issue_type,
        "severity": severity,
        "cue_index": cue_index,
        "other_index": other_index,
        "timecode": timecode,
        "message": message,
        "value": value,
        "threshold": threshold,
    }


def _number_setting(
    name: str,
    value: float,
    *,
    allow_zero: bool,
) -> float:
    """Return a finite numeric setting or raise a useful ``ValueError``."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    if result < 0 or (result == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "greater than zero"
        raise ValueError(f"{name} must be {qualifier}")
    return result


def _integer_setting(name: str, value: int) -> int:
    """Return a positive integer setting or raise ``ValueError``."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _validate_settings(
    max_cps: float,
    max_lines: int,
    max_chars_per_line: int,
    min_duration: float,
    max_duration: float,
    min_gap: float,
) -> tuple[float, float, float, int, int, float]:
    """Validate and normalise all diagnostic thresholds."""
    cps_limit = _number_setting("max_cps", max_cps, allow_zero=False)
    duration_min = _number_setting("min_duration", min_duration, allow_zero=True)
    duration_max = _number_setting("max_duration", max_duration, allow_zero=False)
    line_limit = _integer_setting("max_lines", max_lines)
    length_limit = _integer_setting("max_chars_per_line", max_chars_per_line)
    gap_min = _number_setting("min_gap", min_gap, allow_zero=True)
    if duration_max < duration_min:
        raise ValueError("max_duration must be greater than or equal to min_duration")
    return cps_limit, duration_min, duration_max, line_limit, length_limit, gap_min


def _valid_timing(cue: Cue) -> bool:
    """Whether a cue has finite, ordered, non-negative timing values."""
    start = cue.start
    end = cue.end
    return (
        isinstance(start, (int, float))
        and not isinstance(start, bool)
        and isinstance(end, (int, float))
        and not isinstance(end, bool)
        and math.isfinite(float(start))
        and math.isfinite(float(end))
        and start >= 0
        and end >= start
    )


def _display_index(cue: Cue) -> int | None:
    """Return an index safe for report output, even for a mutated cue."""
    if isinstance(cue.index, int) and not isinstance(cue.index, bool):
        return cue.index
    return None


def run_diagnostics(
    track: Track,
    *,
    max_cps: float = DEFAULT_MAX_CPS,
    max_lines: int = DEFAULT_MAX_LINES,
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
    min_duration: float = DEFAULT_MIN_DURATION,
    max_duration: float = DEFAULT_MAX_DURATION,
    min_gap: float = DEFAULT_MIN_GAP,
) -> List[dict]:
    """Find common structural, timing, readability, and layout issues.

    Rows consistently include ``issue_type``, ``severity``, ``cue_index``,
    ``other_index``, ``timecode``, ``message``, ``value``, and ``threshold``.
    Limits are inclusive, so values exactly on them pass.  Pair checks cover
    source ordering, all overlaps (including nested cues), and adjacent gaps.
    An empty track returns one error and consequently scores zero.
    """
    if not isinstance(track, Track):
        raise TypeError("track must be a Track")

    (
        cps_limit,
        duration_min,
        duration_max,
        line_limit,
        length_limit,
        gap_min,
    ) = _validate_settings(
        max_cps,
        max_lines,
        max_chars_per_line,
        min_duration,
        max_duration,
        min_gap,
    )

    if not track.cues:
        return [
            _issue(
                "empty_track",
                SEVERITY_ERROR,
                None,
                "Track contains no cues",
                value=0,
                threshold=1,
            )
        ]

    issues: List[dict] = []
    seen_indices: dict[int, Cue] = {}
    valid_timed: list[tuple[int, Cue]] = []

    def add(
        issue_type: str,
        severity: str,
        cue_index: int | None,
        message: str,
        **details: Any,
    ) -> None:
        issues.append(_issue(issue_type, severity, cue_index, message, **details))

    for position, cue in enumerate(track.cues):
        if not isinstance(cue, Cue):
            raise TypeError(f"track.cues[{position}] must be a Cue")

        cue_index = _display_index(cue)
        if cue_index is None or cue_index <= 0:
            add(
                "invalid_index",
                SEVERITY_ERROR,
                cue_index,
                "Cue index must be a positive integer",
                value=cue_index,
                threshold=1,
            )
        elif cue_index in seen_indices:
            add(
                "duplicate_index",
                SEVERITY_ERROR,
                cue_index,
                f"Cue index {cue_index} is duplicated",
                other_index=seen_indices[cue_index].index,
                value=cue_index,
            )
        else:
            seen_indices[cue_index] = cue

        if not _valid_timing(cue):
            add(
                "invalid_timing",
                SEVERITY_ERROR,
                cue_index,
                "Cue timing must be finite, non-negative, and end at or after start",
            )
            continue

        valid_timed.append((position, cue))
        tc = format_timecode(cue.start)
        duration = cue.duration

        if not isinstance(cue.text, str):
            plain_text = ""
            lines: list[str] = []
        else:
            plain_text = cue.plain_text
            lines = [strip_all_tags(line).strip() for line in cue.text.splitlines()]
            lines = [line for line in lines if line]

        if not plain_text.strip():
            add(
                "empty_text",
                SEVERITY_ERROR,
                cue_index,
                "Cue has no visible text",
                timecode=tc,
                value=0,
                threshold=1,
            )

        if duration == 0:
            add(
                "zero_duration",
                SEVERITY_ERROR,
                cue_index,
                "Cue has zero duration",
                timecode=tc,
                value=duration,
                threshold=duration_min,
            )
        elif duration < duration_min:
            add(
                "short_duration",
                SEVERITY_WARNING,
                cue_index,
                f"Cue duration {duration:.3f}s is below {duration_min:.3f}s",
                timecode=tc,
                value=duration,
                threshold=duration_min,
            )
        elif duration > duration_max:
            add(
                "long_duration",
                SEVERITY_WARNING,
                cue_index,
                f"Cue duration {duration:.3f}s exceeds {duration_max:.3f}s",
                timecode=tc,
                value=duration,
                threshold=duration_max,
            )

        if duration > 0 and plain_text.strip() and cue.cps > cps_limit:
            add(
                "high_cps",
                SEVERITY_WARNING,
                cue_index,
                f"Reading speed {cue.cps:.2f} CPS exceeds {cps_limit:.2f} CPS",
                timecode=tc,
                value=cue.cps,
                threshold=cps_limit,
            )

        if len(lines) > line_limit:
            add(
                "too_many_lines",
                SEVERITY_WARNING,
                cue_index,
                f"Cue has {len(lines)} lines; maximum is {line_limit}",
                timecode=tc,
                value=len(lines),
                threshold=line_limit,
            )

        longest_line = max((len(line) for line in lines), default=0)
        if longest_line > length_limit:
            add(
                "long_line",
                SEVERITY_WARNING,
                cue_index,
                f"Longest line has {longest_line} characters; maximum is {length_limit}",
                timecode=tc,
                value=longest_line,
                threshold=length_limit,
            )

    # Pair checks use source order for ordering, then chronology for timing.
    for (_, previous), (_, current) in zip(valid_timed, valid_timed[1:]):
        if previous.start > current.start:
            add(
                "out_of_order",
                SEVERITY_ERROR,
                _display_index(previous),
                "Cue appears before an earlier-starting cue in source order",
                other_index=_display_index(current),
                timecode=format_timecode(previous.start),
                value=round(previous.start - current.start, 3),
                threshold=0.0,
            )

    chronological = [
        cue for _, cue in sorted(valid_timed, key=lambda item: (item[1].start, item[0]))
    ]

    # Check every possible overlap, including cues nested inside a long cue.
    for left_position, left in enumerate(chronological):
        for right in chronological[left_position + 1 :]:
            if right.start >= left.end:
                break
            overlap = min(left.end, right.end) - right.start
            if overlap > 0:
                add(
                    "overlap",
                    SEVERITY_ERROR,
                    _display_index(left),
                    f"Cues overlap by {overlap:.3f}s",
                    other_index=_display_index(right),
                    timecode=format_timecode(right.start),
                    value=round(overlap, 3),
                    threshold=0.0,
                )

    if gap_min > 0:
        frontier = chronological[0] if chronological else None
        for right in chronological[1:]:
            assert frontier is not None
            gap = right.start - frontier.end
            if 0 <= gap < gap_min:
                add(
                    "short_gap",
                    SEVERITY_INFO,
                    _display_index(frontier),
                    f"Gap between cues is {gap:.3f}s; minimum is {gap_min:.3f}s",
                    other_index=_display_index(right),
                    timecode=format_timecode(frontier.end),
                    value=round(gap, 3),
                    threshold=gap_min,
                )
            if right.end > frontier.end:
                frontier = right

    return issues


def health_score(
    track: Track,
    *,
    max_cps: float = DEFAULT_MAX_CPS,
    max_lines: int = DEFAULT_MAX_LINES,
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
    min_duration: float = DEFAULT_MIN_DURATION,
    max_duration: float = DEFAULT_MAX_DURATION,
    min_gap: float = DEFAULT_MIN_GAP,
) -> dict[str, int | float]:
    """Return a 0-100 score (errors cost 15, warnings 5, and info 1).

    Deductions are capped at 100; an empty track always scores zero.
    """
    issues = run_diagnostics(
        track,
        max_cps=max_cps,
        min_duration=min_duration,
        max_duration=max_duration,
        max_lines=max_lines,
        max_chars_per_line=max_chars_per_line,
        min_gap=min_gap,
    )
    counts = {
        severity: sum(1 for issue in issues if issue["severity"] == severity)
        for severity in (SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO)
    }
    raw_deduction = sum(SEVERITY_PENALTIES[issue["severity"]] for issue in issues)
    if any(issue["issue_type"] == "empty_track" for issue in issues):
        raw_deduction = 100.0
    deduction = round(min(100.0, raw_deduction), 1)
    return {
        "score": round(100.0 - deduction, 1),
        "total_issues": len(issues),
        "errors": counts[SEVERITY_ERROR],
        "warnings": counts[SEVERITY_WARNING],
        "info": counts[SEVERITY_INFO],
        "deductions": deduction,
    }


def issue_summary(
    track: Track,
    *,
    max_cps: float = DEFAULT_MAX_CPS,
    max_lines: int = DEFAULT_MAX_LINES,
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
    min_duration: float = DEFAULT_MIN_DURATION,
    max_duration: float = DEFAULT_MAX_DURATION,
    min_gap: float = DEFAULT_MIN_GAP,
) -> List[dict]:
    """Group diagnostics by type, sorting by severity and then type name."""
    issues = run_diagnostics(
        track,
        max_cps=max_cps,
        min_duration=min_duration,
        max_duration=max_duration,
        max_lines=max_lines,
        max_chars_per_line=max_chars_per_line,
        min_gap=min_gap,
    )
    grouped: dict[str, dict[str, Any]] = {}
    for issue in issues:
        issue_type = issue["issue_type"]
        if issue_type not in grouped:
            grouped[issue_type] = {
                "issue_type": issue_type,
                "count": 0,
                "severity": issue["severity"],
            }
        grouped[issue_type]["count"] += 1

    return sorted(
        grouped.values(),
        key=lambda row: (_SEVERITY_ORDER[row["severity"]], row["issue_type"]),
    )
