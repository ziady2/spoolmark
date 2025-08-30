"""Time shifting and scaling utilities for tracks."""

from __future__ import annotations

import math

from .cue import Cue
from .errors import ValidationError
from .timing import snap_to_frame
from .track import Track


def _finite_number(value: float, field: str) -> float:
    """Validate and return one finite numeric function argument."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValidationError(field, f"must be a finite number, got {value!r}")
    return float(value)


def shift_track(track: Track, offset: float) -> Track:
    """Return a copy of *track* with every cue shifted by *offset* seconds.

    Parameters
    ----------
    track:
        Source track.
    offset:
        Seconds to shift (positive = later, negative = earlier).
    """
    offset = _finite_number(offset, "offset")
    return track.shift(offset)


def scale_track(track: Track, factor: float) -> Track:
    """Return a copy of *track* with all timings scaled by *factor*.

    A factor of ``1.1`` makes the track 10 % longer; ``0.9`` makes
    it 10 % shorter.
    """
    factor = _finite_number(factor, "factor")
    if factor <= 0:
        raise ValidationError("factor", "must be > 0")
    return track.scale(factor)


def sync_to_reference(
    target: Track,
    ref_start: float,
    ref_end: float,
) -> Track:
    """Linearly map *target* cue timings to the given reference range.

    This shifts and scales so that the first cue starts at *ref_start*
    and the last cue ends at *ref_end*.

    Parameters
    ----------
    target:
        The track to synchronise.
    ref_start:
        Desired start time in seconds.
    ref_end:
        Desired end time in seconds.
    """
    ref_start = _finite_number(ref_start, "ref_start")
    ref_end = _finite_number(ref_end, "ref_end")
    if ref_start < 0:
        raise ValidationError("ref_start", "must be >= 0")
    if ref_end <= ref_start:
        raise ValidationError("ref_end", "must be greater than ref_start")

    cues = target.cues
    if not cues:
        return target.copy()
    t_start = min(c.start for c in cues)
    t_end = max(c.end for c in cues)
    t_span = t_end - t_start
    if t_span <= 0:
        raise ValidationError("target", "timed cues must span more than zero seconds")
    r_span = ref_end - ref_start
    factor = r_span / t_span
    shifted_first = target.shift(-t_start)
    scaled = shifted_first.scale(factor)
    return scaled.shift(ref_start)


def snap_to_frames(
    track: Track,
    fps: float = 25.0,
) -> Track:
    """Snap every cue boundary in *track* to the nearest frame edge.

    Parameters
    ----------
    track:
        Source track.
    fps:
        Frame rate to snap to (default 25 fps).
    """
    # Validate even for an empty track, where the loop below would not call
    # the scalar helper.
    snap_to_frame(0.0, fps)
    snapped: list[Cue] = []
    for cue in track.cues:
        s = snap_to_frame(cue.start, fps)
        e = snap_to_frame(cue.end, fps)
        snapped.append(
            Cue(
                cue.index,
                s,
                e,
                cue.text,
                speaker=cue.speaker,
                style=cue.style,
            )
        )
    return Track(
        track.name,
        cues=snapped,
        language=track.language,
        created=track.created,
    )


def clamp_times(
    track: Track,
    *,
    min_time: float = 0.0,
    max_time: float | None = None,
) -> Track:
    """Clamp all cue timings within [*min_time*, *max_time*].

    Cues entirely outside the range are dropped; cues partially
    inside are trimmed to fit.
    """
    min_time = _finite_number(min_time, "min_time")
    if min_time < 0:
        raise ValidationError("min_time", "must be >= 0")
    if max_time is None:
        ceiling = float("inf")
    else:
        ceiling = _finite_number(max_time, "max_time")
        if ceiling <= min_time:
            raise ValidationError("max_time", "must be greater than min_time")
    kept: list[Cue] = []
    for cue in track.cues:
        s = max(cue.start, min_time)
        e = min(cue.end, ceiling)
        if s < e:
            kept.append(
                Cue(
                    cue.index,
                    s,
                    e,
                    cue.text,
                    speaker=cue.speaker,
                    style=cue.style,
                )
            )
    return Track(
        track.name,
        cues=kept,
        language=track.language,
        created=track.created,
    )
