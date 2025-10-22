"""Input validation helpers."""

from __future__ import annotations

import math
import re
from typing import Any

from .errors import TimecodeError, ValidationError
from .timing import parse_timecode


def validate_timecode(value: str) -> float:
    """Parse and validate a timecode string, returning seconds.

    Raises :class:`TimecodeError` if parsing fails.
    """
    try:
        return parse_timecode(value)
    except Exception as exc:
        raise TimecodeError(str(value)) from exc


def validate_cue_data(data: dict[str, Any]) -> list[str]:
    """Validate a raw cue data dict and return a list of error messages.

    An empty list means the data is valid.

    Checks include:
    - ``start`` and ``end`` must be non-negative numbers.
    - ``end`` must be greater than ``start``.
    - ``text`` must be a non-empty string.
    """
    errors: list[str] = []
    start = data.get("start")
    end = data.get("end")
    text = data.get("text")
    start_valid = (
        isinstance(start, (int, float))
        and not isinstance(start, bool)
        and math.isfinite(start)
        and start >= 0
    )
    end_valid = (
        isinstance(end, (int, float))
        and not isinstance(end, bool)
        and math.isfinite(end)
        and end >= 0
    )
    if not start_valid:
        errors.append("start must be a non-negative number")
    if not end_valid:
        errors.append("end must be a non-negative number")
    if start_valid and end_valid:
        assert isinstance(start, (int, float))
        assert isinstance(end, (int, float))
        if end <= start:
            errors.append("end must be greater than start")
    if not isinstance(text, str) or not text.strip():
        errors.append("text must be a non-empty string")
    return errors


def validate_track_data(data: dict[str, Any]) -> list[str]:
    """Validate a raw track data dict and return a list of error messages.

    Checks that ``name`` is a non-empty string and ``cues`` is a list.
    """
    errors: list[str] = []
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string")
    cues = data.get("cues")
    if not isinstance(cues, list):
        errors.append("cues must be a list")
    return errors


def require_non_empty(value: str, field: str = "value") -> str:
    """Ensure *value* is a non-empty string.

    Raises :class:`ValidationError` if *value* is empty or only whitespace.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(field, "must be a non-empty string")
    return value.strip()


def require_positive(value: float, field: str = "value") -> float:
    """Ensure *value* is a positive number.

    Raises :class:`ValidationError` if *value* is zero or negative.
    """
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValidationError(field, f"must be a positive number, got {value!r}")
    return float(value)


def sanitise_string(
    value: str,
    *,
    max_length: int = 1000,
    strip: bool = True,
) -> str:
    """Clean and truncate a user-supplied string.

    Removes control characters, optionally strips whitespace, and
    truncates to *max_length*.

    Parameters
    ----------
    value:
        The raw input string.
    max_length:
        Maximum allowed length after sanitisation.
    strip:
        Whether to strip leading/trailing whitespace.
    """
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    if strip:
        cleaned = cleaned.strip()
    return cleaned[:max_length]
