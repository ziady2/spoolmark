"""Composable query builder for filtering and sorting cues."""

from __future__ import annotations

from typing import Any, Callable, List

from .cue import Cue
from .track import Track


class Query:
    """Fluent query interface for subtitle tracks.

    Usage::

        results = (Query(track)
                   .where_speaker("NARRATOR")
                   .where_max_duration(5.0)
                   .where_max_cps(25)
                   .sort_by("start")
                   .limit(10)
                   .execute())
    """

    def __init__(self, track: Track) -> None:
        self._cues: list[Cue] = list(track.cues)
        self._language = track.language
        self._created = track.created
        self._filters: list[Callable[[Cue], bool]] = []
        self._sort_key: str = ""
        self._sort_reverse: bool = False
        self._limit_n: int = 0
        self._offset_n: int = 0

    def where(self, predicate: Callable[[Cue], bool]) -> "Query":
        """Add a generic filter predicate."""
        self._filters.append(predicate)
        return self

    def where_speaker(self, speaker: str) -> "Query":
        s = speaker.lower()
        return self.where(lambda c: c.speaker.lower() == s)

    def where_style(self, style: str) -> "Query":
        s = style.lower()
        return self.where(lambda c: c.style.lower() == s)

    def where_max_duration(self, seconds: float) -> "Query":
        return self.where(lambda c: c.duration <= seconds)

    def where_min_duration(self, seconds: float) -> "Query":
        return self.where(lambda c: c.duration >= seconds)

    def where_max_cps(self, cps: float) -> "Query":
        return self.where(lambda c: c.cps <= cps)

    def where_min_cps(self, cps: float) -> "Query":
        return self.where(lambda c: c.cps >= cps)

    def where_contains(self, text: str) -> "Query":
        t = text.lower()
        return self.where(lambda c: t in c.plain_text.lower())

    def where_after(self, seconds: float) -> "Query":
        return self.where(lambda c: c.start >= seconds)

    def where_before(self, seconds: float) -> "Query":
        return self.where(lambda c: c.end <= seconds)

    def where_min_chars(self, count: int) -> "Query":
        return self.where(lambda c: c.char_count >= count)

    def where_max_chars(self, count: int) -> "Query":
        return self.where(lambda c: c.char_count <= count)

    def where_has_speaker(self) -> "Query":
        return self.where(lambda c: bool(c.speaker))

    def sort_by(self, key: str, *, reverse: bool = False) -> "Query":
        """Sort results by *key* (start, duration, cps, text, index)."""
        self._sort_key = key
        self._sort_reverse = reverse
        return self

    def limit(self, n: int) -> "Query":
        self._limit_n = n
        return self

    def offset(self, n: int) -> "Query":
        self._offset_n = n
        return self

    def execute(self) -> list[Cue]:
        """Apply all filters, sort, and pagination."""
        result = list(self._cues)
        for f in self._filters:
            result = [c for c in result if f(c)]
        if self._sort_key:
            result = _sort_cues(result, self._sort_key, self._sort_reverse)
        if self._offset_n > 0:
            result = result[self._offset_n :]
        if self._limit_n > 0:
            result = result[: self._limit_n]
        return result

    def count(self) -> int:
        """Count matching cues without materialising the full list."""
        return len(self.execute())

    def first(self) -> Cue | None:
        """Return the first matching cue, or *None*."""
        results = self.execute()
        return results[0] if results else None

    def to_rows(self) -> List[dict]:
        """Execute and convert to list of dicts."""
        return [c.to_dict() for c in self.execute()]

    def to_track(self, name: str = "Query Result") -> Track:
        """Execute and wrap in a new Track."""
        cues = self.execute()
        reindexed = [
            Cue(i + 1, c.start, c.end, c.text, speaker=c.speaker, style=c.style)
            for i, c in enumerate(cues)
        ]
        return Track(
            name,
            cues=reindexed,
            language=self._language,
            created=self._created,
        )


def _sort_cues(cues: list[Cue], key: str, reverse: bool) -> list[Cue]:
    """Sort cues by the given key."""

    def _key(c: Cue) -> Any:
        if key == "start":
            return c.start
        if key == "end":
            return c.end
        if key == "duration":
            return c.duration
        if key == "cps":
            return c.cps
        if key == "text":
            return c.plain_text.lower()
        if key == "char_count":
            return c.char_count
        if key == "index":
            return c.index
        return c.start

    return sorted(cues, key=_key, reverse=reverse)
