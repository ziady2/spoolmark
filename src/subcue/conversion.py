"""Format conversion helpers for subtitle timecodes."""

from __future__ import annotations

import math

from .timing import format_timecode, format_timecode_vtt, parse_timecode


def srt_to_vtt(timecode: str) -> str:
    """Convert an SRT timecode (``HH:MM:SS,mmm``) to VTT format (``HH:MM:SS.mmm``).

    Parameters
    ----------
    timecode:
        An SRT-formatted timecode string.
    """
    normalised = timecode.replace(",", ".")
    seconds = parse_timecode(normalised)
    return format_timecode_vtt(seconds)


def vtt_to_srt(timecode: str) -> str:
    """Convert a VTT timecode (``HH:MM:SS.mmm``) to SRT format (``HH:MM:SS,mmm``).

    Parameters
    ----------
    timecode:
        A VTT-formatted timecode string.
    """
    seconds = parse_timecode(timecode)
    srt_tc = format_timecode(seconds)
    return srt_tc.replace(".", ",")


def fps_factor(source_fps: float, target_fps: float) -> float:
    """Compute the scaling factor to convert between frame rates.

    Parameters
    ----------
    source_fps:
        Original frame rate.
    target_fps:
        Desired frame rate.

    Returns
    -------
    float
        Multiplicative factor that preserves frame numbers:
        ``source_fps / target_fps``.
    """
    if (
        isinstance(source_fps, bool)
        or not isinstance(source_fps, (int, float))
        or not math.isfinite(source_fps)
        or source_fps <= 0
    ):
        raise ValueError(f"source_fps must be positive, got {source_fps}")
    if (
        isinstance(target_fps, bool)
        or not isinstance(target_fps, (int, float))
        or not math.isfinite(target_fps)
        or target_fps <= 0
    ):
        raise ValueError(f"target_fps must be positive, got {target_fps}")
    return source_fps / target_fps


def framerate_convert(
    seconds: float,
    source_fps: float,
    target_fps: float,
) -> float:
    """Convert a timestamp from one frame rate to another.

    Parameters
    ----------
    seconds:
        Time value in seconds at *source_fps*.
    source_fps:
        Frame rate of the source material.
    target_fps:
        Frame rate of the target material.
    """
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not math.isfinite(seconds)
        or seconds < 0
    ):
        raise ValueError(f"seconds must be finite and non-negative, got {seconds}")
    factor = fps_factor(source_fps, target_fps)
    return seconds * factor


def batch_convert_srt_to_vtt(
    lines: list[str],
) -> list[str]:
    """Convert SRT arrow-separated timecode lines to VTT format.

    Processes lines of the form ``HH:MM:SS,mmm --> HH:MM:SS,mmm``
    and returns a new list with VTT timecodes.  Non-timecode lines
    are passed through unchanged.
    """
    result: list[str] = []
    for line in lines:
        if " --> " in line and "," in line:
            parts = line.split(" --> ")
            if len(parts) == 2:
                left = srt_to_vtt(parts[0].strip())
                right = srt_to_vtt(parts[1].strip())
                result.append(f"{left} --> {right}")
                continue
        result.append(line)
    return result


def batch_convert_vtt_to_srt(
    lines: list[str],
) -> list[str]:
    """Convert VTT arrow-separated timecode lines to SRT format.

    Processes lines of the form ``HH:MM:SS.mmm --> HH:MM:SS.mmm``
    and returns a new list with SRT timecodes.
    """
    result: list[str] = []
    for line in lines:
        if " --> " in line and "." in line:
            parts = line.split(" --> ")
            if len(parts) == 2:
                left = vtt_to_srt(parts[0].strip())
                right = vtt_to_srt(parts[1].strip())
                result.append(f"{left} --> {right}")
                continue
        result.append(line)
    return result
