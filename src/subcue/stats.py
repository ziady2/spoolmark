"""Statistical analysis helpers for tracks and cue data."""

from __future__ import annotations

from typing import Any, Sequence

from .math_utils import mean, median, percentile, stdev
from .track import Track


def track_stats(track: Track) -> dict[str, Any]:
    """Compute summary statistics for a *Track*.

    Returns a dict with keys for cue count, total duration,
    mean / median / stdev of cue durations and CPS values.
    """
    cues = track.cues
    if not cues:
        return {
            "cue_count": 0,
            "total_duration": 0.0,
            "duration_mean": 0.0,
            "duration_median": 0.0,
            "duration_stdev": 0.0,
            "cps_mean": 0.0,
            "cps_median": 0.0,
        }
    durations = [c.duration for c in cues]
    cps_vals = [c.cps for c in cues if c.cps > 0]
    result: dict[str, Any] = {
        "cue_count": len(cues),
        "total_duration": track.duration,
        "duration_mean": mean(durations),
        "duration_median": median(durations),
        "duration_stdev": stdev(durations),
        "cps_mean": mean(cps_vals) if cps_vals else 0.0,
        "cps_median": median(cps_vals) if cps_vals else 0.0,
    }
    return result


def correlation(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Compute Pearson correlation coefficient between *xs* and *ys*.

    Returns ``0.0`` when either sequence has zero variance or the
    sequences differ in length.
    """
    if len(xs) != len(ys):
        return 0.0
    n = len(xs)
    if n < 2:
        return 0.0
    mx = mean(list(xs[:n]))
    my = mean(list(ys[:n]))
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    dx = sum((xs[i] - mx) ** 2 for i in range(n))
    dy = sum((ys[i] - my) ** 2 for i in range(n))
    denom = (dx * dy) ** 0.5
    if denom == 0:
        return 0.0
    return num / denom


def percentile_table(
    values: Sequence[float],
    quantiles: Sequence[float] | None = None,
) -> list[dict[str, float]]:
    """Build a table of percentile break-points for *values*.

    Parameters
    ----------
    values:
        Numeric values to analyse.
    quantiles:
        Percentile levels to compute (defaults to common quintiles).
    """
    if quantiles is None:
        quantiles = [0.0, 0.25, 0.5, 0.75, 1.0]
    data = sorted(values)
    rows: list[dict[str, float]] = []
    for q in quantiles:
        rows.append({"quantile": q, "value": percentile(data, q * 100.0)})
    return rows


def outlier_rows(
    values: Sequence[float],
    *,
    factor: float = 1.5,
) -> list[dict[str, Any]]:
    """Identify outlier values using the IQR method.

    Returns a list of dicts with the index and value of each outlier.

    Parameters
    ----------
    values:
        Data points to inspect.
    factor:
        IQR multiplier for the fence (default 1.5).
    """
    data = sorted(values)
    if len(data) < 4:
        return []
    q1 = percentile(data, 25.0)
    q3 = percentile(data, 75.0)
    iqr = q3 - q1
    lo = q1 - factor * iqr
    hi = q3 + factor * iqr
    result: list[dict[str, Any]] = []
    for idx, v in enumerate(values):
        if v < lo or v > hi:
            result.append({"index": idx, "value": v, "fence": "low" if v < lo else "high"})
    return result
