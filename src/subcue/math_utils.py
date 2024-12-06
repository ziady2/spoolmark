"""Numeric helpers used across subcue."""

from __future__ import annotations

import math
from typing import Sequence


def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        low, high = high, low
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    p = clamp(p, 0, 100)
    xs = sorted(values)
    n = len(xs)
    if n == 1:
        return xs[0]
    rank = (p / 100) * (n - 1)
    lo = int(math.floor(rank))
    hi = min(lo + 1, n - 1)
    frac = rank - lo
    return xs[lo] + (xs[hi] - xs[lo]) * frac


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    n = len(xs)
    mid = n // 2
    if n % 2 == 0:
        return (xs[mid - 1] + xs[mid]) / 2
    return xs[mid]


def stdev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / len(values))


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b != 0 else default


def round_to(value: float, decimals: int = 2) -> float:
    return round(value, decimals)


def cumulative_sum(values: Sequence[float]) -> list[float]:
    result: list[float] = []
    total = 0.0
    for v in values:
        total += v
        result.append(round(total, 6))
    return result


def bucket(value: float, boundaries: Sequence[float]) -> int:
    for i, b in enumerate(boundaries):
        if value < b:
            return i
    return len(boundaries)


def simple_linear_regression(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have equal length")
    n = len(xs)
    if n < 2:
        raise ValueError("need at least two data points")
    x_mean, y_mean = mean(xs), mean(ys)
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    if den == 0:
        return (0.0, y_mean)
    slope = num / den
    return (round(slope, 6), round(y_mean - slope * x_mean, 6))


def weighted_average(values: Sequence[float], weights: Sequence[float]) -> float:
    if len(values) != len(weights):
        raise ValueError("values and weights must have equal length")
    tw = sum(weights)
    if tw == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / tw
