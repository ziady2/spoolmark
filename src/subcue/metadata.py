"""Metadata model for subtitle files."""

from __future__ import annotations

from typing import Any


class Metadata:
    __slots__ = (
        "title",
        "language",
        "author",
        "source",
        "fps",
        "encoding",
        "format_version",
        "created",
        "notes",
    )

    def __init__(
        self,
        *,
        title: str = "",
        language: str = "",
        author: str = "",
        source: str = "",
        fps: float = 0.0,
        encoding: str = "utf-8",
        format_version: str = "",
        created: str = "",
        notes: str = "",
    ) -> None:
        self.title = title.strip()
        self.language = language.strip().lower()
        self.author = author.strip()
        self.source = source.strip()
        self.fps = fps
        self.encoding = encoding.strip().lower()
        self.format_version = format_version.strip()
        self.created = created.strip()
        self.notes = notes.strip()

    def __repr__(self) -> str:
        return f"Metadata(title={self.title!r}, lang={self.language!r})"

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Metadata":
        return cls(**{k: data[k] for k in cls.__slots__ if k in data})

    def copy(self) -> "Metadata":
        return Metadata.from_dict(self.to_dict())

    def is_empty(self) -> bool:
        text_fields = (
            "title",
            "language",
            "author",
            "source",
            "format_version",
            "created",
            "notes",
        )
        has_text = any(getattr(self, key) for key in text_fields)
        has_custom_encoding = self.encoding not in ("", "utf-8")
        return not (has_text or self.fps > 0 or has_custom_encoding)

    def merge(self, other: "Metadata") -> "Metadata":
        """Merge with *other*, preferring non-empty values from *other*."""
        d = self.to_dict()
        for k, v in other.to_dict().items():
            if v and (k != "fps" or v > 0):
                d[k] = v
        return Metadata.from_dict(d)


def detect_language_hint(text: str) -> str:
    """Heuristic language detection based on character ranges."""
    for ch in text:
        cp = ord(ch)
        if 0x0600 <= cp <= 0x06FF:
            return "ar"
        if 0x4E00 <= cp <= 0x9FFF:
            return "zh"
        if 0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF:
            return "ja"
        if 0xAC00 <= cp <= 0xD7AF:
            return "ko"
        if 0x0400 <= cp <= 0x04FF:
            return "ru"
    return "en"
