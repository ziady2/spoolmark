"""Timeline manipulation and analysis utilities."""

from __future__ import annotations

import math
from typing import List

from .cue import Cue
from .track import Track


def timeline_coverage(track: Track) -> float:
    """Calculate what fraction of total time has subtitles.

    Returns a value between 0.0 and 1.0.
    """
    if not track.cues:
        return 0.0
    intervals = _merged_intervals(track.cues)
    total_span = intervals[-1][1] - intervals[0][0]
    if total_span <= 0:
        return 0.0
    covered = sum(end - start for start, end in intervals)
    return round(covered / total_span, 3)


def timeline_gaps(track: Track) -> List[dict]:
    """Return all gaps in the timeline.

    Each dict: ``start``, ``end``, ``duration``.
    """
    intervals = _merged_intervals(track.cues)
    gaps: List[dict] = []
    for (_, gap_start), (gap_end, _) in zip(intervals, intervals[1:]):
        gaps.append(
            {
                "start": round(gap_start, 3),
                "end": round(gap_end, 3),
                "duration": round(gap_end - gap_start, 3),
            }
        )
    return gaps


def timeline_density(track: Track, interval: float = 10.0) -> List[dict]:
    """Compute subtitle density per time interval.

    Each dict: ``interval_start``, ``interval_end``, ``cue_count``, ``char_count``.
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
    sc = track.sorted_cues()
    end_time = max(c.end for c in sc)
    results: List[dict] = []
    start_time = min(c.start for c in sc)
    # Avoid ``floor(start / interval)``: the quotient can overflow even when
    # both inputs are finite.  ``fmod`` computes the same bucket anchor without
    # constructing that potentially enormous quotient.
    t = start_time - math.fmod(start_time, interval)
    if t + interval <= t or end_time + interval <= end_time:
        raise ValueError("interval is too small to advance at this timeline's timestamps")
    while t < end_time:
        t_end = t + interval
        if t_end <= t:
            # Defensive guard against a loss of floating-point progress after
            # several additions.  It is preferable to fail than loop forever.
            raise ValueError("interval is too small to advance at this timeline's timestamps")
        interval_end = min(t_end, end_time)
        cues_in = [c for c in sc if c.start < t_end and c.end > t]
        chars = sum(c.char_count for c in cues_in)
        results.append(
            {
                "interval_start": t,
                "interval_end": interval_end,
                "cue_count": len(cues_in),
                "char_count": chars,
            }
        )
        t = t_end
    return results


def _merged_intervals(cues: List[Cue]) -> list[tuple[float, float]]:
    """Return the union of cue time ranges in chronological order."""
    ordered = sorted(((c.start, c.end) for c in cues), key=lambda item: item[0])
    if not ordered:
        return []
    merged: list[tuple[float, float]] = [ordered[0]]
    for start, end in ordered[1:]:
        previous_start, previous_end = merged[-1]
        if start <= previous_end:
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged


def find_silence_periods(track: Track, min_silence: float = 3.0) -> List[dict]:
    """Find periods with no subtitles lasting at least *min_silence* seconds."""
    if (
        isinstance(min_silence, bool)
        or not isinstance(min_silence, (int, float))
        or not math.isfinite(min_silence)
        or min_silence < 0
    ):
        raise ValueError("min_silence must be a finite non-negative number")
    gaps = timeline_gaps(track)
    return [g for g in gaps if g["duration"] >= min_silence]


def compress_timeline(track: Track, *, remove_gaps: bool = True) -> Track:
    """Remove or shrink gaps between cues.

    If *remove_gaps* is True, cues are packed back-to-back
    with a minimal 0.04s gap.
    """
    if not remove_gaps:
        return track.copy()
    sc = track.sorted_cues()
    if not sc:
        return track.copy()
    min_gap = 0.04
    new_cues: list[Cue] = []
    current_time = sc[0].start
    for cue in sc:
        duration = cue.end - cue.start
        new_start = current_time
        new_end = new_start + duration
        new_cues.append(
            Cue(
                len(new_cues) + 1,
                new_start,
                new_end,
                cue.text,
                speaker=cue.speaker,
                style=cue.style,
            )
        )
        current_time = new_end + min_gap
    return Track(
        track.name,
        cues=new_cues,
        language=track.language,
        created=track.created,
    )


def stretch_to_fill(track: Track, target_duration: float) -> Track:
    """Scale track to fill *target_duration* seconds."""
    if (
        isinstance(target_duration, bool)
        or not isinstance(target_duration, (int, float))
        or not math.isfinite(target_duration)
        or target_duration <= 0
    ):
        raise ValueError("target_duration must be a finite number greater than zero")
    if not track.cues:
        return track.copy()
    start_time = min(cue.start for cue in track.cues)
    end_time = max(cue.end for cue in track.cues)
    source_duration = end_time - start_time
    if source_duration <= 0:
        return track.copy()
    factor = target_duration / source_duration
    return track.scale(factor)


def align_to_keyframes(track: Track, keyframes: list[float], *, threshold: float = 0.1) -> Track:
    """Snap cue start times to nearest keyframe within *threshold*."""
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(threshold)
        or threshold < 0
    ):
        raise ValueError("threshold must be a finite non-negative number")
    if any(
        isinstance(keyframe, bool)
        or not isinstance(keyframe, (int, float))
        or not math.isfinite(keyframe)
        or keyframe < 0
        for keyframe in keyframes
    ):
        raise ValueError("keyframes must contain finite non-negative numbers")
    new_cues: list[Cue] = []
    for cue in track.cues:
        best_start = cue.start
        candidates = [kf for kf in keyframes if abs(kf - cue.start) <= threshold]
        if candidates:
            best_start = min(candidates, key=lambda keyframe: (abs(keyframe - cue.start), keyframe))
        duration = cue.end - cue.start
        new_cues.append(
            Cue(
                cue.index,
                best_start,
                best_start + duration,
                cue.text,
                speaker=cue.speaker,
                style=cue.style,
            )
        )
    return Track(
        track.name,
        cues=new_cues,
        language=track.language,
        created=track.created,
    )
