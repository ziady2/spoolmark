"""Color manipulation class."""

from __future__ import annotations


class Color:
    """Immutable RGB colour value with manipulation helpers.

    Channels are stored as floats in the range 0.0 \u2013 1.0.
    """

    __slots__ = ("r", "g", "b")

    def __init__(self, r: float, g: float, b: float) -> None:
        self.r = max(0.0, min(r, 1.0))
        self.g = max(0.0, min(g, 1.0))
        self.b = max(0.0, min(b, 1.0))

    # -- constructors --------------------------------------------------

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Create a *Color* from a ``#RRGGBB`` hex string."""
        h = hex_str.lstrip("#")
        if len(h) == 3:
            h = h[0] * 2 + h[1] * 2 + h[2] * 2
        if len(h) != 6:
            raise ValueError(f"Invalid hex colour: {hex_str!r}")
        ri = int(h[0:2], 16) / 255.0
        gi = int(h[2:4], 16) / 255.0
        bi = int(h[4:6], 16) / 255.0
        return cls(ri, gi, bi)

    # -- serialisation -------------------------------------------------

    def to_hex(self) -> str:
        """Return the colour as a ``#RRGGBB`` string."""
        ri = round(self.r * 255)
        gi = round(self.g * 255)
        bi = round(self.b * 255)
        return f"#{ri:02x}{gi:02x}{bi:02x}"

    def __repr__(self) -> str:
        return f"Color({self.r:.3f}, {self.g:.3f}, {self.b:.3f})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return (self.r, self.g, self.b) == (other.r, other.g, other.b)

    # -- manipulations -------------------------------------------------

    def _blend(self, factor: float) -> "Color":
        """Blend towards white (*factor* > 0) or black (*factor* < 0)."""
        if factor >= 0:
            nr = self.r + (1.0 - self.r) * factor
            ng = self.g + (1.0 - self.g) * factor
            nb = self.b + (1.0 - self.b) * factor
        else:
            f = 1.0 + factor
            nr = self.r * f
            ng = self.g * f
            nb = self.b * f
        return Color(nr, ng, nb)

    def lighten(self, amount: float = 0.2) -> "Color":
        """Return a lighter variant (0.0 = unchanged, 1.0 = white)."""
        return self._blend(max(0.0, min(amount, 1.0)))

    def darken(self, amount: float = 0.2) -> "Color":
        """Return a darker variant (0.0 = unchanged, 1.0 = black)."""
        return self._blend(-max(0.0, min(amount, 1.0)))

    def luminance(self) -> float:
        """Return the relative luminance (ITU-R BT.709)."""

        def _lin(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * _lin(self.r) + 0.7152 * _lin(self.g) + 0.0722 * _lin(self.b)

    def contrast_text(self) -> "Color":
        """Return black or white depending on background luminance."""
        return Color(0.0, 0.0, 0.0) if self.luminance() > 0.179 else Color(1.0, 1.0, 1.0)

    @staticmethod
    def gradient(start: "Color", end: "Color", steps: int) -> list["Color"]:
        """Generate a list of *steps* colours linearly interpolated between *start* and *end*.

        Parameters
        ----------
        start:
            Starting colour.
        end:
            Ending colour.
        steps:
            Number of colours to produce (minimum 2).
        """
        if steps < 2:
            return [start]
        result: list[Color] = []
        for i in range(steps):
            t = i / (steps - 1)
            r = start.r + (end.r - start.r) * t
            g = start.g + (end.g - start.g) * t
            b = start.b + (end.b - start.b) * t
            result.append(Color(r, g, b))
        return result
