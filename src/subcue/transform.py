"""Cue and track transformation utilities."""

from __future__ import annotations

from typing import Callable, Sequence

from .cue import Cue
from .text_utils import strip_all_tags
from .track import Track


def sort_cues(
    cues: Sequence[Cue],
    *,
    key: str = "start",
    reverse: bool = False,
) -> list[Cue]:
    """Return cues sorted by the given attribute *key*.

    Parameters
    ----------
    cues:
        Cue objects to sort.
    key:
        Cue attribute name to sort on (e.g. ``'start'``, ``'end'``, ``'index'``).
    reverse:
        Sort descending when ``True``.
    """
    ordered = sorted(cues, key=lambda c: getattr(c, key, 0), reverse=reverse)
    return [cue.copy() for cue in ordered]


def filter_cues(
    cues: Sequence[Cue],
    predicate: Callable[[Cue], bool],
) -> list[Cue]:
    """Return only the cues for which *predicate* returns ``True``.

    Parameters
    ----------
    cues:
        Source cue sequence.
    predicate:
        A callable that accepts a *Cue* and returns a bool.
    """
    return [cue.copy() for cue in cues if predicate(cue)]


def strip_tags_from_track(track: Track) -> Track:
    """Return a copy of *track* with all HTML/SSA tags removed from cue text.

    Each cue's text is passed through :func:`strip_all_tags`.
    The original track is not modified.
    """
    cleaned_cues: list[Cue] = []
    for cue in track.cues:
        cleaned_cues.append(
            Cue(
                cue.index,
                cue.start,
                cue.end,
                strip_all_tags(cue.text),
                speaker=cue.speaker,
                style=cue.style,
            )
        )
    return Track(
        track.name,
        cues=cleaned_cues,
        language=track.language,
        created=track.created,
    )


def unique_speakers(cues: Sequence[Cue]) -> list[str]:
    """Return a sorted list of unique speaker labels found in *cues*.

    Cues without a speaker are silently skipped.
    """
    seen: set[str] = set()
    for c in cues:
        if c.speaker:
            seen.add(c.speaker)
    return sorted(seen)


def renumber_cues(cues: Sequence[Cue], start: int = 1) -> list[Cue]:
    """Return copies of *cues* with sequential indices starting at *start*.

    Parameters
    ----------
    cues:
        Source cue sequence.
    start:
        First index number.
    """
    result: list[Cue] = []
    for i, cue in enumerate(cues, start=start):
        c = cue.copy()
        object.__setattr__(c, "index", i)
        result.append(c)
    return result


def filter_by_duration(
    cues: Sequence[Cue],
    *,
    min_dur: float = 0.0,
    max_dur: float = float("inf"),
) -> list[Cue]:
    """Keep only cues whose duration is within [*min_dur*, *max_dur*].

    Parameters
    ----------
    min_dur:
        Minimum duration in seconds.
    max_dur:
        Maximum duration in seconds.
    """
    return [cue.copy() for cue in cues if min_dur <= cue.duration <= max_dur]
