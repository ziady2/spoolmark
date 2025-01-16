"""Marker model for chapter/scene markers."""

from __future__ import annotations

import math
from typing import Any

from .errors import ValidationError


def _finite_number(value: float, field: str) -> float:
    """Validate and coerce a real numeric value without leaking overflow errors."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(field, f"must be a finite number, got {value!r}")
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValidationError(field, f"must be a finite number, got {value!r}") from exc
    if not math.isfinite(result):
        raise ValidationError(field, f"must be a finite number, got {value!r}")
    return result


class Marker:
    __slots__ = ("time", "label", "marker_type", "notes")

    def __init__(
        self, time: float, label: str, *, marker_type: str = "chapter", notes: str = ""
    ) -> None:
        time_value = _finite_number(time, "time")
        if time_value < 0:
            raise ValidationError("time", f"must be a finite non-negative number, got {time!r}")
        if not isinstance(label, str):
            raise ValidationError("label", "must be a string")
        if not label.strip():
            raise ValidationError("label", "must not be empty")
        if not isinstance(marker_type, str):
            raise ValidationError("marker_type", "must be a string")
        if not isinstance(notes, str):
            raise ValidationError("notes", "must be a string")
        self.time = time_value
        self.label = label.strip()
        self.marker_type = marker_type.strip().lower()
        self.notes = notes.strip()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Marker):
            return NotImplemented
        return (self.time, self.label) == (other.time, other.label)

    def __hash__(self) -> int:
        return hash((self.time, self.label))

    def __repr__(self) -> str:
        return f"Marker({self.time:.1f}s, {self.label!r})"

    def __lt__(self, other: "Marker") -> bool:
        return self.time < other.time

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "label": self.label,
            "marker_type": self.marker_type,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Marker":
        try:
            time = float(data.get("time", 0))
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValidationError(
                "time", f"must be a finite number, got {data.get('time')!r}"
            ) from exc
        return cls(
            time=time,
            label=str(data.get("label", "")),
            marker_type=str(data.get("marker_type", "chapter")),
            notes=str(data.get("notes", "")),
        )

    def copy(self) -> "Marker":
        return Marker(self.time, self.label, marker_type=self.marker_type, notes=self.notes)

    def shift(self, offset: float) -> "Marker":
        offset_value = _finite_number(offset, "offset")
        return Marker(
            max(0.0, self.time + offset_value),
            self.label,
            marker_type=self.marker_type,
            notes=self.notes,
        )


def markers_in_range(markers: list[Marker], start: float, end: float) -> list[Marker]:
    return [m for m in markers if start <= m.time <= end]


def cues_between_markers(cues: list, m1: "Marker", m2: "Marker") -> list:
    return [c for c in cues if m1.time <= c.start < m2.time]


def auto_chapter_markers(cues: list, interval: float = 300.0) -> list[Marker]:
    """Generate chapter markers every *interval* seconds."""
    try:
        interval_value = _finite_number(interval, "interval")
    except ValidationError as exc:
        raise ValidationError("interval", "must be a finite number greater than zero") from exc
    if interval_value <= 0:
        raise ValidationError("interval", "must be a finite number greater than zero")
    if not cues:
        return []
    end_time = max(c.end for c in cues)
    markers: list[Marker] = []
    t = 0.0
    idx = 1
    while t < end_time:
        markers.append(Marker(t, f"Chapter {idx}", marker_type="chapter"))
        t += interval_value
        idx += 1
    return markers
