"""SVG timeline and chart rendering utilities."""

from __future__ import annotations

from typing import Sequence

from .text_utils import escape_html


def _svg_open(width: int, height: int) -> str:
    """Return an opening ``<svg>`` tag."""
    safe_width = escape_html(str(width))
    safe_height = escape_html(str(height))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{safe_width}" height="{safe_height}" '
        f'viewBox="0 0 {safe_width} {safe_height}">'
    )


def _rect(x: float, y: float, w: float, h: float, fill: str) -> str:
    """Return an SVG ``<rect>`` element string."""
    safe_fill = escape_html(str(fill))
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{safe_fill}"/>'


def _text_el(x: float, y: float, content: str, size: int = 12) -> str:
    """Return an SVG ``<text>`` element string."""
    safe = escape_html(content)
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}">{safe}</text>'


def svg_bar_chart(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    width: int = 600,
    bar_height: int = 24,
    gap: int = 4,
    color: str = "#4682b4",
) -> str:
    """Render a horizontal bar chart as an SVG string.

    Parameters
    ----------
    labels:
        Category labels for each bar.
    values:
        Numeric values corresponding to each label.
    """
    if not values:
        return _svg_open(width, 20) + "</svg>"
    max_val = max(values) if max(values) > 0 else 1.0
    label_offset = 120
    chart_w = width - label_offset - 20
    total_h = len(values) * (bar_height + gap) + gap
    parts: list[str] = [_svg_open(width, total_h)]
    for i, (label, val) in enumerate(zip(labels, values)):
        y = i * (bar_height + gap) + gap
        bw = max(0.0, (val / max_val) * chart_w)
        parts.append(_text_el(4, y + bar_height - 6, str(label)))
        parts.append(_rect(label_offset, y, bw, bar_height, color))
        parts.append(_text_el(label_offset + bw + 4, y + bar_height - 6, f"{val:.1f}"))
    parts.append("</svg>")
    return "\n".join(parts)


def svg_timeline(
    starts: Sequence[float],
    ends: Sequence[float],
    *,
    width: int = 800,
    row_height: int = 18,
    color: str = "#3366cc",
) -> str:
    """Render time intervals as horizontal bars on a timeline.

    *starts* and *ends* are in seconds.
    """
    if not starts or not ends:
        return _svg_open(width, 20) + "</svg>"
    t_min = min(starts)
    t_max = max(ends) if ends else t_min + 1
    span = t_max - t_min if t_max != t_min else 1.0
    padding = 10
    chart_w = width - 2 * padding
    height = len(starts) * (row_height + 2) + 2 * padding
    parts: list[str] = [_svg_open(width, height)]
    for i, (s, e) in enumerate(zip(starts, ends)):
        x = padding + ((s - t_min) / span) * chart_w
        w = max(((e - s) / span) * chart_w, 1)
        y = padding + i * (row_height + 2)
        parts.append(_rect(x, y, w, row_height, color))
    parts.append("</svg>")
    return "\n".join(parts)


def svg_line_chart(
    values: Sequence[float],
    *,
    width: int = 600,
    height: int = 200,
    color: str = "#228b22",
    stroke_width: int = 2,
) -> str:
    """Render a simple SVG line chart from *values*.

    Values are evenly spaced along the x-axis.
    """
    if len(values) < 2:
        return _svg_open(width, height) + "</svg>"
    pad = 10
    chart_w = width - 2 * pad
    chart_h = height - 2 * pad
    lo = min(values)
    hi = max(values)
    spread = hi - lo if hi != lo else 1.0
    step = chart_w / (len(values) - 1)
    points: list[str] = []
    for i, v in enumerate(values):
        x = pad + i * step
        y = pad + chart_h - ((v - lo) / spread) * chart_h
        points.append(f"{x:.1f},{y:.1f}")
    safe_color = escape_html(str(color))
    safe_stroke_width = escape_html(str(stroke_width))
    polyline = (
        f'<polyline points="{" ".join(points)}" '
        f'fill="none" stroke="{safe_color}" stroke-width="{safe_stroke_width}"/>'
    )
    return "\n".join([_svg_open(width, height), polyline, "</svg>"])
