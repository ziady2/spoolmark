"""Theme definitions for report styling."""

from __future__ import annotations

from typing import Any

from .color import Color


class Theme:
    """Named collection of colours and style tokens.

    Attributes
    ----------
    name:
        Human-readable theme identifier.
    bg:
        Background colour.
    fg:
        Foreground / text colour.
    accent:
        Accent colour for highlights.
    muted:
        Muted colour for secondary text.
    border:
        Border colour.
    """

    def __init__(
        self,
        name: str,
        *,
        bg: Color,
        fg: Color,
        accent: Color,
        muted: Color,
        border: Color,
    ) -> None:
        self.name = name
        self.bg = bg
        self.fg = fg
        self.accent = accent
        self.muted = muted
        self.border = border

    def css_variables(self) -> str:
        """Return a CSS ``:root`` block with custom properties."""
        lines = [
            ":root {",
            f"  --bg: {self.bg.to_hex()};",
            f"  --fg: {self.fg.to_hex()};",
            f"  --accent: {self.accent.to_hex()};",
            f"  --muted: {self.muted.to_hex()};",
            f"  --border: {self.border.to_hex()};",
            "}",
        ]
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        """Serialise the theme to a plain dict."""
        return {
            "name": self.name,
            "bg": self.bg.to_hex(),
            "fg": self.fg.to_hex(),
            "accent": self.accent.to_hex(),
            "muted": self.muted.to_hex(),
            "border": self.border.to_hex(),
        }

    def __repr__(self) -> str:
        return f"Theme({self.name!r})"


LIGHT = Theme(
    "light",
    bg=Color.from_hex("#ffffff"),
    fg=Color.from_hex("#1a1a1a"),
    accent=Color.from_hex("#0066cc"),
    muted=Color.from_hex("#888888"),
    border=Color.from_hex("#cccccc"),
)

DARK = Theme(
    "dark",
    bg=Color.from_hex("#1e1e1e"),
    fg=Color.from_hex("#d4d4d4"),
    accent=Color.from_hex("#569cd6"),
    muted=Color.from_hex("#808080"),
    border=Color.from_hex("#333333"),
)

_REGISTRY: dict[str, Theme] = {
    "light": LIGHT,
    "dark": DARK,
}


def get_theme(name: str) -> Theme:
    """Return a built-in theme by *name*.

    Raises ``KeyError`` when the name is not registered.
    """
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise KeyError(f"Unknown theme {name!r}; choose from {available}")
    return _REGISTRY[name]


def register_theme(theme: Theme) -> None:
    """Register a custom *Theme* for later retrieval via :func:`get_theme`."""
    _REGISTRY[theme.name] = theme
