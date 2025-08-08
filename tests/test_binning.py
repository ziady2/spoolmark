"""Tests for binning."""

from __future__ import annotations

from subcue.binning import (
    Sequence,
    custom_bins,
    equal_width_bins,
    histogram_text,
    percentile,
    quantile_bins,
)


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_custom_bins:
    def test_callable(self):
        assert callable(custom_bins)


class Test_equal_width_bins:
    def test_callable(self):
        assert callable(equal_width_bins)


class Test_histogram_text:
    def test_callable(self):
        assert callable(histogram_text)


class Test_percentile:
    def test_callable(self):
        assert callable(percentile)


class Test_quantile_bins:
    def test_callable(self):
        assert callable(quantile_bins)

    def test_bins_cover_all_values(self):
        bins = quantile_bins([0, 10, 20, 30, 40], n_bins=4)
        assert sum(item["count"] for item in bins) == 5
        assert [item["lo"] for item in bins] == [0.0, 10.0, 20.0, 30.0]
