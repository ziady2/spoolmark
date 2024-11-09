"""Timecode parsing and arithmetic – the core of subtitle processing."""

from __future__ import annotations

import math
import re

from .errors import TimecodeError

# 00:01:23,456  (SRT)  or  00:01:23.456  (VTT/ASS)
_TC_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})")
# Compact: 1:23.456 or 1:23,456
_TC_SHORT_RE = re.compile(r"(\d{1,2}):(\d{2})[,.](\d{1,3})")


def parse_timecode(raw: str) -> float:
    """Parse a timecode string into seconds (float).

    Accepts ``HH:MM:SS,mmm``, ``HH:MM:SS.mmm``, ``MM:SS.mmm``.
    """
    if not isinstance(raw, str):
        raise TimecodeError(str(raw), "expected a string")
    raw = raw.strip()
    m = _TC_RE.fullmatch(raw)
    if m:
        h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        if mi >= 60 or s >= 60:
            raise TimecodeError(raw, "minutes and seconds must be between 00 and 59")
        ms_val = int(ms.ljust(3, "0")[:3])
        return h * 3600 + mi * 60 + s + ms_val / 1000
    m = _TC_SHORT_RE.fullmatch(raw)
    if m:
        mi, s, ms = int(m.group(1)), int(m.group(2)), m.group(3)
        if mi >= 60 or s >= 60:
            raise TimecodeError(raw, "minutes and seconds must be between 00 and 59")
        ms_val = int(ms.ljust(3, "0")[:3])
        return mi * 60 + s + ms_val / 1000
    # Try plain seconds
    try:
        seconds = float(raw)
    except ValueError:
        raise TimecodeError(raw) from None
    if not math.isfinite(seconds) or seconds < 0:
        raise TimecodeError(raw, "seconds must be finite and non-negative")
    return seconds


def _finite_number(value: float, name: str) -> float:
    """Return *value* as a finite float, rejecting booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def format_timecode(seconds: float, *, separator: str = ",") -> str:
    """Format seconds as ``HH:MM:SS,mmm``."""
    seconds = _finite_number(seconds, "seconds")
    if seconds < 0:
        seconds = 0.0
    total_ms = round(seconds * 1000)
    h = total_ms // 3_600_000
    remainder = total_ms % 3_600_000
    mi = remainder // 60_000
    remainder = remainder % 60_000
    s = remainder // 1000
    ms = remainder % 1000
    return f"{h:02d}:{mi:02d}:{s:02d}{separator}{ms:03d}"


def format_timecode_vtt(seconds: float) -> str:
    """Format seconds as ``HH:MM:SS.mmm`` (WebVTT style)."""
    return format_timecode(seconds, separator=".")


def format_timecode_ass(seconds: float) -> str:
    """Format seconds as ``H:MM:SS.cc`` (ASS centiseconds)."""
    seconds = _finite_number(seconds, "seconds")
    if seconds < 0:
        seconds = 0.0
    total_cs = round(seconds * 100)
    h = total_cs // 360_000
    remainder = total_cs % 360_000
    mi = remainder // 6000
    remainder = remainder % 6000
    s = remainder // 100
    cs = remainder % 100
    return f"{h}:{mi:02d}:{s:02d}.{cs:02d}"


def timecode_to_ms(seconds: float) -> int:
    """Convert seconds to integer milliseconds."""
    seconds = _finite_number(seconds, "seconds")
    return round(seconds * 1000)


def ms_to_timecode(ms: int) -> float:
    """Convert milliseconds to seconds."""
    return _finite_number(ms, "milliseconds") / 1000


def duration_between(start: float, end: float) -> float:
    """Absolute duration between two timecodes in seconds."""
    return abs(_finite_number(end, "end") - _finite_number(start, "start"))


def shift_time(seconds: float, offset: float) -> float:
    """Shift a timecode by *offset* seconds (may be negative)."""
    return max(0.0, _finite_number(seconds, "seconds") + _finite_number(offset, "offset"))


def scale_time(seconds: float, factor: float) -> float:
    """Scale a timecode by *factor* (for frame-rate conversions)."""
    seconds = _finite_number(seconds, "seconds")
    factor = _finite_number(factor, "factor")
    if factor <= 0:
        raise ValueError("factor must be greater than zero")
    return max(0.0, seconds * factor)


def overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    """Return overlap duration in seconds (0 if no overlap)."""
    start_a = _finite_number(start_a, "start_a")
    end_a = _finite_number(end_a, "end_a")
    start_b = _finite_number(start_b, "start_b")
    end_b = _finite_number(end_b, "end_b")
    lo = max(start_a, start_b)
    hi = min(end_a, end_b)
    return max(0.0, hi - lo)


def gap(end_a: float, start_b: float) -> float:
    """Return the gap between two consecutive cues (may be negative if overlap)."""
    return _finite_number(start_b, "start_b") - _finite_number(end_a, "end_a")


def snap_to_frame(seconds: float, fps: float = 24.0) -> float:
    """Snap a timecode to the nearest frame boundary."""
    seconds = _finite_number(seconds, "seconds")
    fps = _finite_number(fps, "fps")
    if fps <= 0:
        raise ValueError("fps must be greater than zero")
    frame = round(seconds * fps)
    return frame / fps


def cps(text: str, duration: float) -> float:
    """Characters per second (excluding whitespace-only lines)."""
    duration = _finite_number(duration, "duration")
    clean = text.replace("\\n", " ").replace("\n", " ").strip()
    if duration <= 0 or not clean:
        return 0.0
    return round(len(clean) / duration, 2)


def wps(text: str, duration: float) -> float:
    """Words per second."""
    duration = _finite_number(duration, "duration")
    words = text.replace("\\n", " ").replace("\n", " ").split()
    if duration <= 0 or not words:
        return 0.0
    return round(len(words) / duration, 2)


def format_duration_human(seconds: float) -> str:
    """Human-readable duration like '1m 23s' or '45s'."""
    seconds = _finite_number(seconds, "seconds")
    if seconds < 0:
        return "0s"
    total = round(seconds)
    if total < 60:
        return f"{total}s"
    m, s = divmod(total, 60)
    if m < 60:
        return f"{m}m {s}s" if s else f"{m}m"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"
