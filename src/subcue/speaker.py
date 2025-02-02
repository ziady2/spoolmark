"""Speaker model for dialogue attribution."""

from __future__ import annotations

from typing import Any

from .errors import ValidationError


class Speaker:
    __slots__ = ("name", "voice_id", "color", "language")

    def __init__(
        self, name: str, *, voice_id: str = "", color: str = "", language: str = ""
    ) -> None:
        name = name.strip()
        if not name:
            raise ValidationError("name", "speaker name must not be empty")
        self.name = name
        self.voice_id = voice_id.strip()
        self.color = color.strip().lower()
        self.language = language.strip().lower()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Speaker):
            return NotImplemented
        return self.name.lower() == other.name.lower()

    def __hash__(self) -> int:
        return hash(self.name.lower())

    def __repr__(self) -> str:
        return f"Speaker({self.name!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "voice_id": self.voice_id,
            "color": self.color,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Speaker":
        return cls(
            name=str(data.get("name", "")),
            voice_id=str(data.get("voice_id", "")),
            color=str(data.get("color", "")),
            language=str(data.get("language", "")),
        )

    def copy(self) -> "Speaker":
        return Speaker(self.name, voice_id=self.voice_id, color=self.color, language=self.language)

    def display(self) -> str:
        parts = [self.name]
        if self.language:
            parts.append(f"[{self.language}]")
        return " ".join(parts)


def extract_speakers(cues: list) -> list[Speaker]:
    """Build a unique speaker list from cues with speaker attributes."""
    seen: dict[str, Speaker] = {}
    for cue in cues:
        s = getattr(cue, "speaker", "")
        if s and s.lower() not in seen:
            seen[s.lower()] = Speaker(s)
    return sorted(seen.values(), key=lambda sp: sp.name.lower())
