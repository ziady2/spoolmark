"""Tests for math_utils."""

from __future__ import annotations

import pytest

from subcue.math_utils import (
    bucket,
    clamp,
    cumulative_sum,
    lerp,
    mean,
    median,
    percentile,
    safe_divide,
    simple_linear_regression,
    stdev,
    weighted_average,
)


class TestClamp:
    @pytest.mark.parametrize("v,lo,hi,exp", [(5, 0, 10, 5), (-1, 0, 10, 0), (15, 0, 10, 10)])
    def test_basic(self, v, lo, hi, exp):
        assert clamp(v, lo, hi) == exp


class TestLerp:
    def test_basic(self):
        assert lerp(0, 10, 0.5) == 5


class TestPercentile:
    def test_median(self):
        assert percentile([1, 2, 3, 4, 5], 50) == 3

    def test_empty(self):
        assert percentile([], 50) == 0.0


class TestMeanMedian:
    def test_mean(self):
        assert mean([2, 4, 6]) == 4.0

    def test_median_odd(self):
        assert median([1, 3, 5]) == 3

    def test_median_even(self):
        assert median([1, 2, 3, 4]) == 2.5


class TestStdev:
    def test_basic(self):
        s = stdev([2, 4, 4, 4, 5, 5, 7, 9])
        assert 1.5 < s < 2.5

    def test_single(self):
        assert stdev([5]) == 0.0


class TestSafeDivide:
    def test_normal(self):
        assert safe_divide(10, 2) == 5

    def test_zero(self):
        assert safe_divide(10, 0) == 0.0


class TestCumulativeSum:
    def test_basic(self):
        assert cumulative_sum([1, 2, 3]) == [1, 3, 6]


class TestBucket:
    def test_basic(self):
        assert bucket(15, [10, 20, 30]) == 1


class TestRegression:
    def test_basic(self):
        slope, _ = simple_linear_regression([1, 2, 3], [2, 4, 6])
        assert abs(slope - 2) < 0.01

    def test_too_few(self):
        with pytest.raises(ValueError):
            simple_linear_regression([1], [2])


class TestWeightedAverage:
    def test_basic(self):
        assert weighted_average([10, 20], [1, 3]) == 17.5
