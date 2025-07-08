"""Table formatting utilities and a builder class."""

from __future__ import annotations

from typing import Any, Sequence

from .text_utils import pad_left, pad_right


class TableBuilder:
    """Incrementally build a text table.

    Usage::

        tb = TableBuilder(["Name", "Score"])
        tb.add_row(["Alice", "92"])
        tb.add_row(["Bob", "87"])
        print(tb.render())
    """

    def __init__(self, headers: Sequence[str]) -> None:
        self._headers: list[str] = list(headers)
        self._rows: list[list[str]] = []
        self._align: list[str] = ["left"] * len(headers)

    def set_alignment(self, index: int, align: str) -> None:
        """Set column *index* alignment ('left' or 'right')."""
        if 0 <= index < len(self._align):
            self._align[index] = align

    def add_row(self, row: Sequence[Any]) -> None:
        """Append a data row (values are converted to strings)."""
        self._rows.append([str(v) for v in row])

    def _col_widths(self) -> list[int]:
        widths = [len(h) for h in self._headers]
        for row in self._rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(cell))
        return widths

    def _format_row(self, cells: Sequence[str], widths: list[int]) -> str:
        parts: list[str] = []
        for i, cell in enumerate(cells):
            w = widths[i] if i < len(widths) else len(cell)
            if i < len(self._align) and self._align[i] == "right":
                parts.append(pad_left(cell, w))
            else:
                parts.append(pad_right(cell, w))
        return " | ".join(parts)

    def render(self) -> str:
        """Return the complete table as a multi-line string."""
        widths = self._col_widths()
        header = self._format_row(self._headers, widths)
        sep = "-+-".join("-" * w for w in widths)
        body = "\n".join(self._format_row(r, widths) for r in self._rows)
        return f"{header}\n{sep}\n{body}"


def format_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
) -> str:
    """One-shot helper to build and render a table string."""
    tb = TableBuilder(headers)
    for r in rows:
        tb.add_row(r)
    return tb.render()


def transpose(
    rows: Sequence[Sequence[Any]],
) -> list[list[Any]]:
    """Transpose *rows* so columns become rows and vice-versa.

    All inner sequences should have the same length.
    """
    if not rows:
        return []
    return [list(col) for col in zip(*rows)]


def pivot_table(
    rows: Sequence[dict[str, Any]],
    row_key: str,
    col_key: str,
    value_key: str,
) -> list[dict[str, Any]]:
    """Pivot *rows* by *row_key* and *col_key*.

    Returns a list of dicts where each dict has the *row_key* value
    as a key and one key per unique *col_key* value.
    """
    col_values: list[str] = sorted({str(r[col_key]) for r in rows})
    grouped: dict[str, dict[str, Any]] = {}
    for r in rows:
        rk = str(r[row_key])
        if rk not in grouped:
            grouped[rk] = {row_key: rk}
        grouped[rk][str(r[col_key])] = r.get(value_key, "")
    result: list[dict[str, Any]] = []
    for rk in sorted(grouped):
        entry = grouped[rk]
        for cv in col_values:
            entry.setdefault(cv, "")
        result.append(entry)
    return result
