"""Comprehensive track summary report."""

from __future__ import annotations

from typing import List

from .math_utils import mean, median, percentile, stdev
from .track import Track


def full_summary(track: Track) -> dict:
    """Generate a comprehensive summary of a track.

    Returns a dictionary with sections: general, timing, cps, speakers.
    """
    if not track.cues:
        return {
            "name": track.name,
            "language": track.language,
            "cue_count": 0,
            "total_duration": 0.0,
            "total_chars": 0,
            "total_words": 0,
            "timing": {
                "avg_duration": 0.0,
                "median_duration": 0.0,
                "stdev_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "p90_duration": 0.0,
            },
            "cps": {
                "avg_cps": 0.0,
                "median_cps": 0.0,
                "max_cps": 0.0,
                "high_cps_count": 0,
            },
            "speakers": {
                "unique_speakers": 0,
                "speaker_distribution": {},
                "dialogue_ratio": 0.0,
            },
            "quality": {
                "score": 0.0,
                "overlaps": 0,
                "high_cps": 0,
                "short_cues": 0,
                "long_cues": 0,
            },
        }

    durations = [c.duration for c in track.cues]
    cps_vals = [c.cps for c in track.cues if c.duration > 0]
    char_counts = [c.char_count for c in track.cues]
    word_counts = [c.word_count for c in track.cues]

    return {
        "name": track.name,
        "language": track.language,
        "cue_count": len(track),
        "total_duration": round(track.duration, 2),
        "total_chars": sum(char_counts),
        "total_words": sum(word_counts),
        "timing": {
            "avg_duration": round(mean(durations), 3),
            "median_duration": round(median(durations), 3),
            "stdev_duration": round(stdev(durations), 3),
            "min_duration": round(min(durations), 3),
            "max_duration": round(max(durations), 3),
            "p90_duration": round(percentile(durations, 90), 3),
        },
        "cps": {
            "avg_cps": round(mean(cps_vals), 2) if cps_vals else 0,
            "median_cps": round(median(cps_vals), 2) if cps_vals else 0,
            "max_cps": round(max(cps_vals), 2) if cps_vals else 0,
            "high_cps_count": sum(1 for v in cps_vals if v > 25),
        },
        "speakers": _speaker_info(track),
        "quality": _quality_info(track),
    }


def summary_rows(tracks: list[Track]) -> List[dict]:
    """Generate a comparison row for each track.

        Keys: `
    ``name``, ``cues``, ``duration``, ``avg_cps``, ``max_cps``,
        ``overlaps``, ``quality_score``.
    """
    results: List[dict] = []
    for track in tracks:
        cps_vals = [c.cps for c in track.cues if c.duration > 0]
        overlaps = len(track.overlapping_pairs())
        quality = _quality_score(track)
        results.append(
            {
                "name": track.name,
                "cues": len(track),
                "duration": round(track.duration, 2),
                "avg_cps": round(mean(cps_vals), 2) if cps_vals else 0,
                "max_cps": round(max(cps_vals), 2) if cps_vals else 0,
                "overlaps": overlaps,
                "quality_score": quality,
            }
        )
    results.sort(key=lambda r: r["quality_score"], reverse=True)
    return results


def quality_breakdown(track: Track) -> List[dict]:
    """Detailed quality breakdown per check.

    Keys: ``check``, ``passed``, ``total``, ``score``.
    """
    if not track.cues:
        return []

    checks: List[dict] = []

    # CPS check
    cps_ok = sum(1 for c in track.cues if c.cps <= 25)
    checks.append(
        {
            "check": "CPS <= 25",
            "passed": cps_ok,
            "total": len(track),
            "score": round(cps_ok / len(track) * 100, 1),
        }
    )

    # Duration check
    dur_ok = sum(1 for c in track.cues if 0.7 <= c.duration <= 7.0)
    checks.append(
        {
            "check": "Duration 0.7-7s",
            "passed": dur_ok,
            "total": len(track),
            "score": round(dur_ok / len(track) * 100, 1),
        }
    )

    # Line count check
    line_ok = sum(1 for c in track.cues if c.line_count <= 2)
    checks.append(
        {
            "check": "Max 2 lines",
            "passed": line_ok,
            "total": len(track),
            "score": round(line_ok / len(track) * 100, 1),
        }
    )

    # Overlap check
    overlapping_cues = {id(cue) for pair in track.overlapping_pairs() for cue in pair}
    non_overlap = sum(1 for cue in track.cues if id(cue) not in overlapping_cues)
    checks.append(
        {
            "check": "No overlaps",
            "passed": non_overlap,
            "total": len(track),
            "score": round(non_overlap / len(track) * 100, 1),
        }
    )

    return checks


def _speaker_info(track: Track) -> dict:
    """Collect speaker statistics."""
    speakers: dict[str, int] = {}
    for cue in track.cues:
        if cue.speaker:
            speakers[cue.speaker] = speakers.get(cue.speaker, 0) + 1
    return {
        "unique_speakers": len(speakers),
        "speaker_distribution": speakers,
        "dialogue_ratio": round(sum(1 for c in track.cues if c.speaker) / max(len(track), 1), 3),
    }


def _quality_info(track: Track) -> dict:
    """Calculate quality metrics."""
    return {
        "score": _quality_score(track),
        "overlaps": len(track.overlapping_pairs()),
        "high_cps": sum(1 for c in track.cues if c.cps > 25),
        "short_cues": sum(1 for c in track.cues if c.duration < 0.7),
        "long_cues": sum(1 for c in track.cues if c.duration > 7.0),
    }


def _quality_score(track: Track) -> float:
    """Compute an overall quality score (0-100)."""
    if not track.cues:
        return 0.0
    n = len(track)
    score = 100.0
    # Penalty for overlaps
    score -= len(track.overlapping_pairs()) * 5
    # Penalty for high CPS
    score -= sum(1 for c in track.cues if c.cps > 25) / n * 20
    # Penalty for bad durations
    score -= sum(1 for c in track.cues if c.duration < 0.7 or c.duration > 7) / n * 15
    return round(max(0, min(100, score)), 1)
