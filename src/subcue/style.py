"""Style model for subtitle formatting (SSA/ASS compatible)."""

from __future__ import annotations

from typing import Any

from .errors import ValidationError

ALIGNMENTS = {
    1: "bottom-left",
    2: "bottom-center",
    3: "bottom-right",
    4: "middle-left",
    5: "middle-center",
    6: "middle-right",
    7: "top-left",
    8: "top-center",
    9: "top-right",
}


class Style:
    __slots__ = (
        "name",
        "font_name",
        "font_size",
        "primary_color",
        "bold",
        "italic",
        "underline",
        "alignment",
        "margin_l",
        "margin_r",
        "margin_v",
        "outline",
        "shadow",
    )

    def __init__(
        self,
        name: str = "Default",
        *,
        font_name: str = "Arial",
        font_size: int = 20,
        primary_color: str = "#ffffff",
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        alignment: int = 2,
        margin_l: int = 10,
        margin_r: int = 10,
        margin_v: int = 10,
        outline: float = 2.0,
        shadow: float = 1.0,
    ) -> None:
        if not name.strip():
            raise ValidationError("name", "style name must not be empty")
        if font_size < 1:
            raise ValidationError("font_size", f"must be >= 1, got {font_size}")
        self.name = name.strip()
        self.font_name = font_name.strip()
        self.font_size = font_size
        self.primary_color = primary_color.strip().lower()
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.alignment = alignment
        self.margin_l = margin_l
        self.margin_r = margin_r
        self.margin_v = margin_v
        self.outline = outline
        self.shadow = shadow

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Style):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"Style({self.name!r}, {self.font_name!r}, {self.font_size})"

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Style":
        return cls(**{k: data[k] for k in cls.__slots__ if k in data})

    def copy(self) -> "Style":
        return Style.from_dict(self.to_dict())

    def css(self) -> str:
        parts = [
            f"font-family: {self.font_name}",
            f"font-size: {self.font_size}px",
            f"color: {self.primary_color}",
        ]
        if self.bold:
            parts.append("font-weight: bold")
        if self.italic:
            parts.append("font-style: italic")
        return "; ".join(parts)

    def alignment_label(self) -> str:
        return ALIGNMENTS.get(self.alignment, "bottom-center")
