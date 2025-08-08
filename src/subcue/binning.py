"""Time-based binning and histogram utilities."""

from __future__ import annotations

from typing import Any, Sequence

from .math_utils import percentile


def equal_width_bins(
    values: Sequence[float],
    n_bins: int = 10,
) -> list[dict[str, Any]]:
    """Partition *values* into *n_bins* equal-width bins.

    Returns a list of dicts with ``'lo'``, ``'hi'``, and ``'count'`` keys.
    """
    if not values or n_bins < 1:
        return []
    lo = min(values)
    hi = max(values)
    if lo == hi:
        return [{"lo": lo, "hi": hi, "count": len(values)}]
    width = (hi - lo) / n_bins
    bins: list[dict[str, Any]] = []
    for i in range(n_bins):
        b_lo = lo + i * width
        b_hi = b_lo + width
        count = sum(1 for v in values if b_lo <= v < b_hi)
        if i == n_bins - 1:
            count = sum(1 for v in values if b_lo <= v <= b_hi)
        bins.append({"lo": round(b_lo, 6), "hi": round(b_hi, 6), "count": count})
    return bins


def quantile_bins(
    values: Sequence[float],
    n_bins: int = 4,
) -> list[dict[str, Any]]:
    """Partition *values* into *n_bins* quantile-based bins.

    Each bin contains approximately the same number of items.
    """
    if not values or n_bins < 1:
        return []
    data = sorted(values)
    edges: list[float] = []
    for i in range(n_bins + 1):
        percentile_rank = i / n_bins * 100
        edges.append(percentile(data, percentile_rank))
    bins: list[dict[str, Any]] = []
    for i in range(n_bins):
        b_lo = edges[i]
        b_hi = edges[i + 1]
        if i < n_bins - 1:
            count = sum(1 for v in data if b_lo <= v < b_hi)
        else:
            count = sum(1 for v in data if b_lo <= v <= b_hi)
        bins.append({"lo": round(b_lo, 6), "hi": round(b_hi, 6), "count": count})
    return bins


def custom_bins(
    values: Sequence[float],
    edges: Sequence[float],
) -> list[dict[str, Any]]:
    """Bin *values* using explicit *edges*.

    ``len(edges)`` must be at least 2.  Returns one bin per consecutive
    pair of edges.
    """
    if len(edges) < 2:
        return []
    sorted_edges = sorted(edges)
    bins: list[dict[str, Any]] = []
    for i in range(len(sorted_edges) - 1):
        b_lo = sorted_edges[i]
        b_hi = sorted_edges[i + 1]
        if i < len(sorted_edges) - 2:
            count = sum(1 for v in values if b_lo <= v < b_hi)
        else:
            count = sum(1 for v in values if b_lo <= v <= b_hi)
        bins.append({"lo": round(b_lo, 6), "hi": round(b_hi, 6), "count": count})
    return bins


def histogram_text(
    values: Sequence[float],
    n_bins: int = 10,
    *,
    width: int = 40,
    char: str = "#",
) -> str:
    """Render a simple text histogram for *values*.

    Returns a multi-line string with one row per bin.

    Parameters
    ----------
    values:
        Numeric data points.
    n_bins:
        Number of bins.
    width:
        Maximum bar width in characters.
    char:
        Character used for the bar.
    """
    bins = equal_width_bins(values, n_bins)
    if not bins:
        return "(no data)"
    max_count = max(b["count"] for b in bins)
    lines: list[str] = []
    for b in bins:
        label = f"[{b['lo']:>8.2f}, {b['hi']:>8.2f})"
        bar_len = round(b["count"] / max_count * width) if max_count else 0
        bar_str = char * bar_len
        lines.append(f"{label} | {bar_str} {b['count']}")
    return "\n".join(lines)
