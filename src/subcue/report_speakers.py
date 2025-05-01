"""Speaker distribution and turn analysis report.

Provides statistics on how dialogue is distributed among speakers,
turn-taking patterns, and per-speaker timing.
"""

from __future__ import annotations

from typing import List

from .cue import Cue
from .math_utils import mean, median, round_to
from .timing import format_timecode
from .track import Track


def _speaker_key(speaker: str) -> str:
    """Return the case-insensitive identity used by speaker reports."""
    return speaker.casefold()


def _speaker_labels(cues: List[Cue]) -> dict[str, str]:
    """Map speaker identities to the first spelling found in track order."""
    labels: dict[str, str] = {}
    for cue in cues:
        labels.setdefault(_speaker_key(cue.speaker), cue.speaker)
    return labels


def speaker_distribution(track: Track) -> List[dict]:
    """Count cues and compute timing per speaker.

    Keys
    ----
    speaker : str
        Speaker name (empty string for unattributed cues).
    cue_count : int
        Number of cues for this speaker.
    pct_cues : float
        Percentage of total cues.
    total_duration : float
        Combined duration of the speaker's cues.
    pct_duration : float
        Percentage of total speaking time.
    avg_duration : float
        Average cue duration for the speaker.
    total_chars : int
        Total characters spoken.
    avg_cps : float
        Average characters per second.
    """
    groups: dict[str, List[Cue]] = {}
    labels = _speaker_labels(track.cues)
    for cue in track.cues:
        groups.setdefault(_speaker_key(cue.speaker), []).append(cue)
    total_cues = len(track.cues) or 1
    total_dur = sum(c.duration for c in track.cues) or 1.0
    result: List[dict] = []
    for speaker_key in sorted(groups):
        cues = groups[speaker_key]
        dur = sum(c.duration for c in cues)
        chars = sum(c.char_count for c in cues)
        cps_vals = [c.cps for c in cues if c.duration > 0]
        result.append(
            {
                "speaker": labels[speaker_key],
                "cue_count": len(cues),
                "pct_cues": round_to(len(cues) / total_cues * 100),
                "total_duration": round_to(dur),
                "pct_duration": round_to(dur / total_dur * 100),
                "avg_duration": round_to(mean([c.duration for c in cues])),
                "total_chars": chars,
                "avg_cps": round_to(mean(cps_vals)) if cps_vals else 0.0,
            }
        )
    return result


def speaker_turns(track: Track) -> List[dict]:
    """Analyse speaker turn-taking in cue order.

    A *turn* starts when the speaker changes from one cue to the next.

    Keys
    ----
    turn_number : int
        1-based turn sequence.
    speaker : str
        Speaker for this turn.
    start_tc : str
        Timecode of the first cue in the turn.
    end_tc : str
        Timecode of the last cue in the turn.
    cue_count : int
        Number of consecutive cues in this turn.
    total_duration : float
        Combined duration of cues in this turn.
    total_chars : int
        Total characters spoken during this turn.
    """
    sorted_cues = track.sorted_cues()
    if not sorted_cues:
        return []
    labels = _speaker_labels(track.cues)
    result: List[dict] = []
    turn_cues: List[Cue] = [sorted_cues[0]]
    turn_speaker_key = _speaker_key(sorted_cues[0].speaker)
    turn_num = 1
    for cue in sorted_cues[1:]:
        speaker_key = _speaker_key(cue.speaker)
        if speaker_key != turn_speaker_key:
            result.append(_build_turn(turn_num, turn_cues, labels[turn_speaker_key]))
            turn_num += 1
            turn_cues = [cue]
            turn_speaker_key = speaker_key
        else:
            turn_cues.append(cue)
    if turn_cues:
        result.append(_build_turn(turn_num, turn_cues, labels[turn_speaker_key]))
    return result


def _build_turn(turn_number: int, cues: List[Cue], speaker: str) -> dict:
    """Build a single turn record from a list of consecutive cues."""
    return {
        "turn_number": turn_number,
        "speaker": speaker,
        "start_tc": format_timecode(cues[0].start),
        "end_tc": format_timecode(max(cue.end for cue in cues)),
        "cue_count": len(cues),
        "total_duration": round_to(sum(c.duration for c in cues)),
        "total_chars": sum(c.char_count for c in cues),
    }


def speaker_timing(track: Track) -> List[dict]:
    """Per-speaker timing statistics.

    Keys
    ----
    speaker : str
        Speaker name.
    min_duration : float
        Shortest cue duration.
    max_duration : float
        Longest cue duration.
    median_duration : float
        Median cue duration.
    first_appearance_tc : str
        Timecode of the speaker's first cue.
    last_appearance_tc : str
        Timecode of the speaker's last cue.
    """
    groups: dict[str, List[Cue]] = {}
    labels = _speaker_labels(track.cues)
    for cue in track.sorted_cues():
        groups.setdefault(_speaker_key(cue.speaker), []).append(cue)
    result: List[dict] = []
    for speaker_key in sorted(groups):
        cues = groups[speaker_key]
        durs = [c.duration for c in cues]
        result.append(
            {
                "speaker": labels[speaker_key],
                "min_duration": round_to(min(durs)),
                "max_duration": round_to(max(durs)),
                "median_duration": round_to(median(durs)),
                "first_appearance_tc": format_timecode(cues[0].start),
                "last_appearance_tc": format_timecode(cues[-1].start),
            }
        )
    return result
