"""Tests for interpolation."""

from __future__ import annotations

import math

import pytest

from subcue.interpolation import (
    Sequence,
    clamp,
    exponential_smoothing,
    fill_gaps,
    linear_interpolate,
    moving_average,
    resample,
    trend_direction,
)


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_clamp:
    def test_callable(self):
        assert callable(clamp)


class Test_exponential_smoothing:
    def test_callable(self):
        assert callable(exponential_smoothing)

    @pytest.mark.parametrize("alpha", [math.nan, math.inf, True])
    def test_rejects_invalid_alpha(self, alpha):
        with pytest.raises(ValueError):
            exponential_smoothing([], alpha)


class Test_fill_gaps:
    def test_callable(self):
        assert callable(fill_gaps)

    @pytest.mark.parametrize("step", [0, -0.5, math.nan, math.inf, True])
    def test_rejects_non_positive_step(self, step):
        with pytest.raises(ValueError):
            fill_gaps([0, 1], [0, 1], step)

    def test_rejects_mismatched_series(self):
        with pytest.raises(ValueError):
            fill_gaps([0, 1], [0], 0.5)

    def test_always_includes_the_original_endpoint(self):
        times, values = fill_gaps([0, 1], [0, 10], 0.3)
        assert times[-1] == 1
        assert values[-1] == 10

    @pytest.mark.parametrize(
        ("times", "values"),
        [
            ([0, math.nan], [0, 1]),
            ([0, math.inf], [0, 1]),
            ([0, 1], [0, math.nan]),
            ([0, 1], [0, True]),
        ],
    )
    def test_rejects_non_finite_series(self, times, values):
        with pytest.raises(ValueError):
            fill_gaps(times, values, 0.5)

    def test_rejects_a_step_that_cannot_advance_the_float_clock(self):
        with pytest.raises(ValueError, match="too small"):
            fill_gaps([1e16, 1e16 + 2], [0, 1], 0.1)


class Test_linear_interpolate:
    def test_callable(self):
        assert callable(linear_interpolate)

    def test_rejects_non_finite_inputs(self):
        with pytest.raises(ValueError):
            linear_interpolate(0, 0, 1, 1, math.nan)


class Test_moving_average:
    def test_callable(self):
        assert callable(moving_average)

    def test_rejects_non_positive_window(self):
        with pytest.raises(ValueError):
            moving_average([1, 2], window=0)

    def test_even_window_uses_no_more_than_the_requested_points(self):
        assert moving_average([0, 10, 20], window=2) == [5, 15, 20]

    @pytest.mark.parametrize("window", [2.5, True])
    def test_rejects_non_integer_window(self, window):
        with pytest.raises(ValueError):
            moving_average([1, 2], window=window)


class Test_resample:
    def test_callable(self):
        assert callable(resample)

    def test_rejects_too_short_output(self):
        with pytest.raises(ValueError):
            resample([1, 2], 1)

    @pytest.mark.parametrize("new_length", [2.5, True])
    def test_rejects_non_integer_output_length(self, new_length):
        with pytest.raises(ValueError):
            resample([1, 2], new_length)


class Test_trend_direction:
    def test_callable(self):
        assert callable(trend_direction)

    @pytest.mark.parametrize("value", [math.nan, math.inf, True])
    def test_rejects_invalid_values(self, value):
        with pytest.raises(ValueError):
            trend_direction([1, value, 3])
