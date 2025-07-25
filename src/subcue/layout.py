"""Layout utilities for structured text output."""

from __future__ import annotations

from .text_utils import truncate, wrap_lines


class Section:
    """A titled text section.

    Sections can be rendered as plain text blocks with a header line.
    """

    def __init__(self, title: str, body: str = "") -> None:
        self.title = title
        self.body = body

    def render(self, width: int = 72) -> str:
        """Render the section as a titled text block."""
        underline = "=" * min(len(self.title), width)
        return f"{self.title}\n{underline}\n{self.body}"

    def __repr__(self) -> str:
        return f"Section({self.title!r})"


class Grid:
    """Simple text grid layout arranging cells in rows and columns.

    Usage::

        g = Grid(columns=3, col_width=20)
        g.add("A"); g.add("B"); g.add("C")
        g.add("D")
        print(g.render())
    """

    def __init__(self, columns: int = 3, col_width: int = 20) -> None:
        self.columns = max(1, columns)
        self.col_width = max(4, col_width)
        self._cells: list[str] = []

    def add(self, text: str) -> None:
        """Add a cell to the grid."""
        self._cells.append(truncate(text, self.col_width))

    def render(self) -> str:
        """Return the grid as a multi-line string."""
        lines: list[str] = []
        for i in range(0, len(self._cells), self.columns):
            row_cells = self._cells[i : i + self.columns]
            padded = [c.ljust(self.col_width) for c in row_cells]
            lines.append("  ".join(padded))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Grid(columns={self.columns}, cells={len(self._cells)})"


def horizontal_rule(width: int = 72, char: str = "-") -> str:
    """Return a horizontal rule string of the given *width*."""
    return char * width


def page_header(
    title: str,
    *,
    subtitle: str = "",
    width: int = 72,
) -> str:
    """Return a centred page header with optional subtitle.

    The header is bordered above and below with ``=`` characters.
    """
    border = "=" * width
    centre_title = title.center(width)
    parts = [border, centre_title]
    if subtitle:
        parts.append(subtitle.center(width))
    parts.append(border)
    return "\n".join(parts)


def wrap_text(
    text: str,
    *,
    width: int = 72,
    indent: str = "",
) -> str:
    """Wrap *text* to *width* columns with optional hanging indent.

    Uses :func:`~subcue.text_utils.wrap_lines` internally.
    """
    wrapped = "\n".join(wrap_lines(text, width - len(indent)))
    if not indent:
        return wrapped
    lines = wrapped.splitlines()
    indented = [indent + line for line in lines]
    return "\n".join(indented)


def two_column(
    left: str,
    right: str,
    *,
    total_width: int = 72,
    separator: str = " | ",
) -> str:
    """Format *left* and *right* text in a two-column layout."""
    left_width = (total_width - len(separator)) // 2
    right_width = total_width - left_width - len(separator)
    left_trunc = truncate(left, left_width).ljust(left_width)
    right_trunc = truncate(right, right_width).ljust(right_width)
    return f"{left_trunc}{separator}{right_trunc}"
