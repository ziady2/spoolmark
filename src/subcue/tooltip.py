"""Tooltip text generators for chart hover states."""

from __future__ import annotations

from .cue import Cue
from .formatter import format_cps, format_number, format_percentage
from .timing import format_duration_human, format_timecode_vtt


def cue_tooltip(cue: Cue) -> str:
    """Generate a multi-line tooltip for a subtitle cue."""
    lines = [
        f"Cue #{cue.index}",
        f"Time: {format_timecode_vtt(cue.start)} \u2192 {format_timecode_vtt(cue.end)}",
        f"Duration: {format_duration_human(cue.duration)}",
        f"CPS: {format_cps(cue.cps)}",
        f"Characters: {cue.char_count}",
        f"Words: {cue.word_count}",
    ]
    if cue.speaker:
        lines.insert(1, f"Speaker: {cue.speaker}")
    return "\n".join(lines)


def bar_tooltip(label: str, value: float, total: float) -> str:
    """Tooltip for a bar chart segment."""
    pct = value / total if total else 0
    return f"{label}: {format_number(value)} ({format_percentage(pct)})"


def pie_tooltip(label: str, value: float, total: float) -> str:
    """Tooltip for a pie chart slice."""
    pct = value / total if total else 0
    return f"{label}\n{format_number(value)} ({format_percentage(pct)})"


def timeline_tooltip(cue: Cue) -> str:
    """Short tooltip for a timeline bar."""
    return f"#{cue.index}: {cue.plain_text[:30]}... ({cue.duration:.1f}s)"


def speaker_tooltip(name: str, cue_count: int, total_cues: int) -> str:
    """Tooltip for speaker distribution chart."""
    pct = cue_count / total_cues if total_cues else 0
    return f"{name}\n{cue_count} cues ({format_percentage(pct)})"


def gap_tooltip(index_a: int, index_b: int, gap_sec: float) -> str:
    """Tooltip for a gap indicator."""
    return f"Gap between cue {index_a} and {index_b}\n{gap_sec:.3f}s"


def overlap_tooltip(index_a: int, index_b: int, overlap_sec: float) -> str:
    """Tooltip for an overlap indicator."""
    return f"Overlap: cue {index_a} \u2229 cue {index_b}\n{overlap_sec:.3f}s"


def progress_tooltip(done: int, total: int, label: str = "cues") -> str:
    """Tooltip for progress indicators."""
    pct = done / total if total else 0
    return f"{done}/{total} {label} ({format_percentage(pct)})"


def density_tooltip(
    interval_start: float, interval_end: float, cue_count: int, char_count: int
) -> str:
    """Tooltip for density chart intervals."""
    return (
        f"{format_timecode_vtt(interval_start)} \u2013 {format_timecode_vtt(interval_end)}\n"
        f"{cue_count} cues, {char_count} chars"
    )
