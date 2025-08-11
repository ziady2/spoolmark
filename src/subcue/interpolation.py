"""Timing interpolation and smoothing utilities."""

from __future__ import annotations

import math
from typing import Sequence

from .math_utils import clamp


def _finite_number(value: object, name: str) -> float:
    """Return *value* as a float after strict finite-number validation."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _finite_values(values: Sequence[float], name: str) -> list[float]:
    """Validate a numeric sequence without mutating the caller's data."""
    return [_finite_number(value, f"{name}[{index}]") for index, value in enumerate(values)]


def linear_interpolate(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
) -> float:
    """Return the linearly interpolated y-value at *x*.

    Parameters
    ----------
    x0, y0:  First known point.
    x1, y1:  Second known point.
    x:  The x-value to interpolate at.
    """
    x0 = _finite_number(x0, "x0")
    y0 = _finite_number(y0, "y0")
    x1 = _finite_number(x1, "x1")
    y1 = _finite_number(y1, "y1")
    x = _finite_number(x, "x")
    if x1 == x0:
        return (y0 + y1) / 2.0
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def resample(
    values: Sequence[float],
    new_length: int,
) -> list[float]:
    """Resample *values* to *new_length* using linear interpolation.

    Parameters
    ----------
    values:
        Source data points.
    new_length:
        Desired number of output samples (must be >= 2).
    """
    if isinstance(new_length, bool) or not isinstance(new_length, int) or new_length < 2:
        raise ValueError("new_length must be an integer of at least 2")
    data = _finite_values(values, "values")
    n = len(data)
    if n == 0:
        return [0.0] * new_length
    if n == 1:
        return [data[0]] * new_length
    result: list[float] = []
    for i in range(new_length):
        t = i / (new_length - 1) * (n - 1)
        lo = int(t)
        hi = min(lo + 1, n - 1)
        frac = t - lo
        result.append(data[lo] + frac * (data[hi] - data[lo]))
    return result


def moving_average(
    values: Sequence[float],
    window: int = 3,
) -> list[float]:
    """Compute a simple moving average with the given *window* size.

    The output has the same length as *values*; edges use smaller windows.
    """
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise ValueError("window must be a positive integer")
    data = _finite_values(values, "values")
    n = len(data)
    if n == 0:
        return []
    result: list[float] = []
    left = (window - 1) // 2
    right = window // 2
    for i in range(n):
        lo = max(0, i - left)
        hi = min(n, i + right + 1)
        segment = data[lo:hi]
        result.append(sum(segment) / len(segment))
    return result


def exponential_smoothing(
    values: Sequence[float],
    alpha: float = 0.3,
) -> list[float]:
    """Apply single exponential smoothing.

    Parameters
    ----------
    values:
        Raw data points.
    alpha:
        Smoothing factor in (0, 1). Higher values react faster.
    """
    alpha = clamp(_finite_number(alpha, "alpha"), 0.01, 0.99)
    data = _finite_values(values, "values")
    if not data:
        return []
    result: list[float] = [data[0]]
    for v in data[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


def trend_direction(values: Sequence[float]) -> str:
    """Return ``'rising'``, ``'falling'``, or ``'flat'`` based on linear trend.

    Uses a simple least-squares slope estimate.
    """
    data = _finite_values(values, "values")
    n = len(data)
    if n < 2:
        return "flat"
    x_mean = (n - 1) / 2.0
    y_mean = sum(data) / n
    num = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    if den == 0:
        return "flat"
    slope = num / den
    if abs(slope) < 1e-9:
        return "flat"
    return "rising" if slope > 0 else "falling"


def fill_gaps(
    times: Sequence[float],
    values: Sequence[float],
    step: float,
) -> tuple[list[float], list[float]]:
    """Fill gaps in *times*/*values* by interpolating at *step* intervals.

    Returns new (times, values) lists with evenly-spaced points
    covering the original range.
    """
    step = _finite_number(step, "step")
    if step <= 0:
        raise ValueError("step must be greater than zero")
    if len(times) != len(values):
        raise ValueError("times and values must have equal length")
    clean_times = _finite_values(times, "times")
    clean_values = _finite_values(values, "values")
    if len(clean_times) < 2:
        return clean_times, clean_values
    if any(right <= left for left, right in zip(clean_times, clean_times[1:])):
        raise ValueError("times must be strictly increasing")
    t_min = clean_times[0]
    t_max = clean_times[-1]
    span = t_max - t_min
    if not math.isfinite(span):
        raise ValueError("time range must be finite")
    if t_min + step <= t_min:
        raise ValueError("step is too small to advance at this time magnitude")
    step_count_float = span / step
    if not math.isfinite(step_count_float):
        raise ValueError("step creates too many interpolation points")
    step_count = math.floor(step_count_float)
    new_times: list[float] = []
    new_values: list[float] = []
    idx = 0
    for step_index in range(step_count + 1):
        t = t_min + step_index * step
        if new_times and t <= new_times[-1]:
            raise ValueError("step is too small to produce distinct time points")
        if t > t_max:
            break
        while idx < len(clean_times) - 1 and clean_times[idx + 1] < t:
            idx += 1
        if idx >= len(clean_times) - 1:
            new_values.append(clean_values[-1])
        else:
            y = linear_interpolate(
                clean_times[idx],
                clean_values[idx],
                clean_times[idx + 1],
                clean_values[idx + 1],
                t,
            )
            new_values.append(y)
        new_times.append(t)
    if new_times and math.isclose(new_times[-1], t_max, rel_tol=0.0, abs_tol=1e-12):
        new_times[-1] = t_max
        new_values[-1] = clean_values[-1]
    elif not new_times or new_times[-1] < t_max:
        new_times.append(t_max)
        new_values.append(clean_values[-1])
    return new_times, new_values
