"""Value formatters for human-readable display."""

from __future__ import annotations

import math


def format_number(
    value: float,
    *,
    precision: int = 2,
    thousands_sep: str = ",",
) -> str:
    """Format a numeric *value* with grouping and decimal precision.

    Parameters
    ----------
    value:
        The number to format.
    precision:
        Decimal places to show.
    thousands_sep:
        Character used for thousands grouping.
    """
    if math.isnan(value) or math.isinf(value):
        return str(value)
    formatted = f"{value:,.{precision}f}"
    if thousands_sep != ",":
        formatted = formatted.replace(",", thousands_sep)
    return formatted


def format_duration(seconds: float) -> str:
    """Format *seconds* as ``HH:MM:SS`` or ``MM:SS`` if under one hour.

    Fractional seconds are rounded to the nearest integer.
    """
    total = round(seconds)
    if total < 0:
        total = 0
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_percentage(
    value: float,
    *,
    precision: int = 1,
    symbol: str = "%",
) -> str:
    """Format *value* (0.0 \u2013 1.0) as a percentage string.

    A value of ``0.85`` returns ``'85.0%'`` by default.
    """
    pct = value * 100.0
    return f"{pct:.{precision}f}{symbol}"


def format_timecode_display(seconds: float) -> str:
    """Format *seconds* as ``HH:MM:SS.mmm`` for display purposes.

    Always shows three decimal places for millisecond precision.
    """
    if seconds < 0:
        seconds = 0.0
    total_ms = round(seconds * 1000)
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def format_cps(cps_value: float) -> str:
    """Format a characters-per-second value with a descriptor.

    Returns strings like ``'15.2 cps (normal)'``.
    """
    if cps_value < 0:
        label = "invalid"
    elif cps_value <= 15:
        label = "slow"
    elif cps_value <= 25:
        label = "normal"
    elif cps_value <= 35:
        label = "fast"
    else:
        label = "very fast"
    return f"{cps_value:.1f} cps ({label})"


def format_filesize(size_bytes: int) -> str:
    """Return a human-friendly file-size string (e.g. ``'1.4 MB'``).

    Parameters
    ----------
    size_bytes:
        File size in bytes.
    """
    if size_bytes < 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size_bytes)
    for unit in units[:-1]:
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024.0
    return f"{value:.1f} {units[-1]}"
