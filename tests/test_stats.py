"""Tests for stats."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.stats import (
    Sequence,
    correlation,
    mean,
    median,
    outlier_rows,
    percentile,
    percentile_table,
    stdev,
    track_stats,
)
from subcue.track import Track


def _track():
    return Track(
        "T",
        cues=[
            Cue(1, 0, 2, "Hello world", speaker="A"),
            Cue(2, 3, 6, "Second subtitle here", speaker="B"),
            Cue(3, 7, 8, "Short one", speaker="A"),
        ],
    )


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_correlation:
    def test_callable(self):
        assert callable(correlation)

    def test_mismatched_lengths_return_zero(self):
        assert correlation([1, 2], [1, 2, 3]) == 0.0


class TestTrackStats:
    def test_empty_has_the_same_schema_as_non_empty(self):
        assert track_stats(Track("empty")).keys() == track_stats(_track()).keys()


class Test_mean:
    def test_callable(self):
        assert callable(mean)


class Test_median:
    def test_callable(self):
        assert callable(median)


class Test_outlier_rows:
    def test_callable(self):
        assert callable(outlier_rows)

    def test_uses_true_quartiles(self):
        assert outlier_rows([0, 10, 11, 12, 13]) == [
            {"index": 0, "value": 0, "fence": "low"},
        ]


class Test_percentile:
    def test_callable(self):
        assert callable(percentile)


class Test_percentile_table:
    def test_callable(self):
        assert callable(percentile_table)

    def test_quantiles_are_fractions(self):
        rows = percentile_table([0, 100], [0.0, 0.25, 0.5, 1.0])
        assert [row["value"] for row in rows] == [0.0, 25.0, 50.0, 100.0]


class Test_stdev:
    def test_callable(self):
        assert callable(stdev)
