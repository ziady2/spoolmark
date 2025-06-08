"""ASCII timeline and chart rendering utilities."""

from __future__ import annotations

from typing import Sequence


def bar(
    value: float,
    max_value: float,
    width: int = 40,
    char: str = "#",
) -> str:
    """Return a single horizontal bar whose length is proportional to *value*.

    The bar is drawn within *width* characters using *char*.
    """
    if max_value <= 0:
        return ""
    ratio = max(0.0, min(value / max_value, 1.0))
    filled = round(ratio * width)
    return char * filled + " " * (width - filled)


def sparkline(
    values: Sequence[float], ticks: str = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
) -> str:
    """Build a sparkline string from numeric *values*.

    Each value is mapped to a character from *ticks*.
    """
    if not values:
        return ""
    lo = min(values)
    hi = max(values)
    spread = hi - lo if hi != lo else 1.0
    out: list[str] = []
    for v in values:
        idx = int((v - lo) / spread * (len(ticks) - 1))
        out.append(ticks[idx])
    return "".join(out)


def horizontal_bar_chart(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    width: int = 40,
    char: str = "#",
) -> str:
    """Render a labelled horizontal bar chart.

    Returns a multi-line string with right-aligned labels.
    """
    if not labels or not values:
        return ""
    max_val = max(values) if values else 1.0
    label_w = max(len(str(lb)) for lb in labels)
    lines: list[str] = []
    for label, val in zip(labels, values):
        b = bar(val, max_val, width=width, char=char)
        lines.append(f"{str(label):>{label_w}} | {b} {val:.1f}")
    return "\n".join(lines)


def table_string(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    padding: int = 1,
) -> str:
    """Format a simple ASCII table with column alignment.

    Returns a multi-line string including a header separator line.
    """
    col_widths: list[int] = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    pad = " " * padding

    def _fmt(cells: Sequence[str]) -> str:
        parts: list[str] = []
        for i, cell in enumerate(cells):
            w = col_widths[i] if i < len(col_widths) else len(str(cell))
            parts.append(f"{str(cell):<{w}}")
        return pad + (pad + "|" + pad).join(parts) + pad

    header_line = _fmt(headers)
    sep = "-" * len(header_line)
    body = "\n".join(_fmt(r) for r in rows)
    return f"{header_line}\n{sep}\n{body}"


def progress_bar(
    current: int,
    total: int,
    *,
    width: int = 30,
    filled_char: str = "=",
    empty_char: str = " ",
    brackets: tuple[str, str] = ("[", "]"),
) -> str:
    """Render a progress bar like ``[====      ] 40%``.

    Parameters
    ----------
    current:
        Current progress value.
    total:
        Total expected value (must be > 0 for a meaningful bar).
    """
    pct = max(0.0, min(current / total, 1.0)) if total > 0 else 0.0
    filled = round(pct * width)
    inner = filled_char * filled + empty_char * (width - filled)
    return f"{brackets[0]}{inner}{brackets[1]} {pct:>6.1%}"


def box(text: str, *, width: int = 60, border: str = "*") -> str:
    """Wrap *text* in a decorative ASCII box.

    Lines longer than *width* \u2013 4 are truncated.
    """
    inner_w = width - 4
    top = border * width
    lines = text.splitlines()
    body_lines: list[str] = []
    for line in lines:
        truncated = line[:inner_w]
        padded = truncated + " " * (inner_w - len(truncated))
        body_lines.append(f"{border} {padded} {border}")
    return "\n".join([top] + body_lines + [top])
