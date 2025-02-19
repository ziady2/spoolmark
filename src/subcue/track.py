"""Track model – an ordered sequence of cues."""

from __future__ import annotations

from typing import Any, Iterator

from .cue import Cue
from .errors import NotFoundError


class Track:
    """An ordered collection of :class:`~subcue.cue.Cue` objects.

    Parameters
    ----------
    name:  Track label (e.g. ``"English"``).
    cues:  Ordered list of cues.
    language:  ISO-639 language code.
    """

    __slots__ = ("name", "cues", "language", "created")

    def __init__(
        self,
        name: str = "Untitled",
        *,
        cues: list[Cue] | None = None,
        language: str = "",
        created: str = "",
    ) -> None:
        self.name: str = name.strip()
        self.cues: list[Cue] = list(cues or [])
        self.language: str = language.strip().lower()
        self.created: str = created.strip()

    def __len__(self) -> int:
        return len(self.cues)

    def __iter__(self) -> Iterator[Cue]:
        return iter(self.cues)

    def __getitem__(self, index: int) -> Cue:
        return self.cues[index]

    def __repr__(self) -> str:
        return f"Track({self.name!r}, cues={len(self.cues)})"

    @property
    def duration(self) -> float:
        if not self.cues:
            return 0.0
        first_start = min(c.start for c in self.cues)
        last_end = max(c.end for c in self.cues)
        return round(last_end - first_start, 3)

    @property
    def total_text_length(self) -> int:
        return sum(c.char_count for c in self.cues)

    def sorted_cues(self) -> list[Cue]:
        return sorted(self.cues, key=lambda c: c.start)

    def reindex(self) -> "Track":
        """Return a copy with cues re-indexed starting from 1."""
        new_cues = [
            Cue(i + 1, c.start, c.end, c.text, speaker=c.speaker, style=c.style)
            for i, c in enumerate(self.sorted_cues())
        ]
        return Track(
            self.name,
            cues=new_cues,
            language=self.language,
            created=self.created,
        )

    def shift(self, offset: float) -> "Track":
        return Track(
            self.name,
            cues=[c.shift(offset) for c in self.cues],
            language=self.language,
            created=self.created,
        )

    def scale(self, factor: float) -> "Track":
        return Track(
            self.name,
            cues=[c.scale(factor) for c in self.cues],
            language=self.language,
            created=self.created,
        )

    def add_cue(self, cue: Cue) -> "Track":
        new = self.copy()
        new.cues.append(cue.copy())
        return new

    def remove_cue(self, index: int) -> "Track":
        new_cues = [c.copy() for c in self.cues if c.index != index]
        if len(new_cues) == len(self.cues):
            raise NotFoundError("cue", str(index))
        return Track(
            self.name,
            cues=new_cues,
            language=self.language,
            created=self.created,
        )

    def filter_by_speaker(self, speaker: str) -> "Track":
        s = speaker.lower()
        cues = [c.copy() for c in self.cues if c.speaker.lower() == s]
        return Track(
            f"{self.name} [{speaker}]",
            cues=cues,
            language=self.language,
            created=self.created,
        )

    def overlapping_pairs(self) -> list[tuple[Cue, Cue]]:
        """Return every pair whose time ranges overlap.

        Checking only adjacent cues misses overlaps when one long cue contains
        several shorter cues.  The chronological early exit keeps the common
        non-overlapping case inexpensive while still reporting nested ranges.
        """
        pairs: list[tuple[Cue, Cue]] = []
        sc = self.sorted_cues()
        for position, left in enumerate(sc):
            for right in sc[position + 1 :]:
                if right.start >= left.end:
                    break
                if left.overlaps(right):
                    pairs.append((left, right))
        return pairs

    def timeline_pairs(self) -> list[tuple[Cue, Cue]]:
        """Pair each cue with the cue defining the covered-time frontier.

        This is the appropriate relationship for measuring silence gaps.  A
        short cue nested inside a longer cue must not make a later silence gap
        appear longer than it really is.
        """
        sc = self.sorted_cues()
        if len(sc) < 2:
            return []
        pairs: list[tuple[Cue, Cue]] = []
        frontier = sc[0]
        for current in sc[1:]:
            pairs.append((frontier, current))
            if current.end > frontier.end:
                frontier = current
        return pairs

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "language": self.language,
            "created": self.created,
            "cues": [c.to_dict() for c in self.cues],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Track":
        cues = [Cue.from_dict(d) for d in data.get("cues", [])]
        return cls(
            name=str(data.get("name", "Untitled")),
            cues=cues,
            language=str(data.get("language", "")),
            created=str(data.get("created", "")),
        )

    def copy(self) -> "Track":
        return Track(
            self.name,
            cues=[c.copy() for c in self.cues],
            language=self.language,
            created=self.created,
        )

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "language": self.language,
            "cue_count": len(self.cues),
            "duration": self.duration,
            "total_chars": self.total_text_length,
        }
