"""Cue model – a single timed subtitle entry."""

from __future__ import annotations

import math
from typing import Any

from .errors import ValidationError
from .text_utils import char_count, line_count, strip_all_tags, word_count
from .timing import cps as calc_cps
from .timing import format_timecode


class Cue:
    """A subtitle cue with start/end times and text content.

    Parameters
    ----------
    index:  1-based sequence number.
    start:  Start time in seconds.
    end:  End time in seconds.
    text:  Subtitle text (may contain newlines and tags).
    speaker:  Optional speaker name.
    style:  Optional style identifier.
    """

    __slots__ = ("index", "start", "end", "text", "speaker", "style")

    def __init__(
        self,
        index: int,
        start: float,
        end: float,
        text: str,
        *,
        speaker: str = "",
        style: str = "",
    ) -> None:
        if isinstance(start, bool) or not isinstance(start, (int, float)):
            raise ValidationError("start", f"must be a finite number, got {start!r}")
        if isinstance(end, bool) or not isinstance(end, (int, float)):
            raise ValidationError("end", f"must be a finite number, got {end!r}")
        if not math.isfinite(start):
            raise ValidationError("start", f"must be a finite number, got {start!r}")
        if not math.isfinite(end):
            raise ValidationError("end", f"must be a finite number, got {end!r}")
        if start < 0:
            raise ValidationError("start", f"must be >= 0, got {start}")
        if end < start:
            raise ValidationError("end", f"must be >= start ({start}), got {end}")
        if not isinstance(text, str):
            raise ValidationError("text", f"must be a string, got {type(text).__name__}")
        if not isinstance(speaker, str):
            raise ValidationError("speaker", f"must be a string, got {type(speaker).__name__}")
        if not isinstance(style, str):
            raise ValidationError("style", f"must be a string, got {type(style).__name__}")
        self.index: int = index
        self.start: float = float(start)
        self.end: float = float(end)
        self.text: str = text
        self.speaker: str = speaker.strip()
        self.style: str = style.strip()

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    @property
    def mid(self) -> float:
        return round((self.start + self.end) / 2, 3)

    @property
    def cps(self) -> float:
        return calc_cps(self.plain_text, self.duration)

    @property
    def plain_text(self) -> str:
        return strip_all_tags(self.text)

    @property
    def char_count(self) -> int:
        return char_count(self.plain_text)

    @property
    def word_count(self) -> int:
        return word_count(self.plain_text)

    @property
    def line_count(self) -> int:
        return line_count(self.text)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cue):
            return NotImplemented
        return (self.start, self.end, self.text) == (other.start, other.end, other.text)

    def __hash__(self) -> int:
        return hash((self.start, self.end, self.text))

    def __repr__(self) -> str:
        tc = f"{format_timecode(self.start)} -> {format_timecode(self.end)}"
        return f"Cue({self.index}, {tc}, {self.plain_text[:30]!r})"

    def __lt__(self, other: "Cue") -> bool:
        return self.start < other.start

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "speaker": self.speaker,
            "style": self.style,
            "duration": self.duration,
            "cps": self.cps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Cue":
        return cls(
            index=int(data.get("index", 0)),
            start=float(data.get("start", 0)),
            end=float(data.get("end", 0)),
            text=str(data.get("text", "")),
            speaker=str(data.get("speaker", "")),
            style=str(data.get("style", "")),
        )

    def copy(self) -> "Cue":
        return Cue(
            self.index, self.start, self.end, self.text, speaker=self.speaker, style=self.style
        )

    def shift(self, offset: float) -> "Cue":
        """Return a copy with times shifted by *offset* seconds."""
        if isinstance(offset, bool) or not isinstance(offset, (int, float)):
            raise ValidationError("offset", f"must be a finite number, got {offset!r}")
        if not math.isfinite(offset):
            raise ValidationError("offset", f"must be a finite number, got {offset!r}")
        new_start = max(0.0, self.start + offset)
        new_end = max(new_start, self.end + offset)
        return Cue(
            self.index, new_start, new_end, self.text, speaker=self.speaker, style=self.style
        )

    def scale(self, factor: float) -> "Cue":
        """Return a copy with times scaled by *factor*."""
        if (
            isinstance(factor, bool)
            or not isinstance(factor, (int, float))
            or not math.isfinite(factor)
            or factor <= 0
        ):
            raise ValidationError("factor", "must be > 0")
        return Cue(
            self.index,
            self.start * factor,
            self.end * factor,
            self.text,
            speaker=self.speaker,
            style=self.style,
        )

    def overlaps(self, other: "Cue") -> bool:
        """Check if this cue overlaps with another."""
        return self.start < other.end and self.end > other.start

    def gap_to(self, other: "Cue") -> float:
        """Return gap in seconds to the next cue (negative = overlap)."""
        return other.start - self.end

    def with_text(self, new_text: str) -> "Cue":
        return Cue(
            self.index, self.start, self.end, new_text, speaker=self.speaker, style=self.style
        )

    def with_speaker(self, new_speaker: str) -> "Cue":
        return Cue(
            self.index, self.start, self.end, self.text, speaker=new_speaker, style=self.style
        )
