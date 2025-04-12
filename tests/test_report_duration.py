"""Tests for report_duration."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.report_duration import duration_buckets, duration_extremes
from subcue.track import Track


def _track():
    return Track(
        "Test",
        cues=[
            Cue(1, 1.0, 4.0, "Hello and welcome.", speaker="NARRATOR"),
            Cue(2, 5.0, 7.5, "Today we discuss subtitles.", speaker="NARRATOR"),
            Cue(3, 8.0, 9.0, "They help accessibility.", speaker="GUEST", style="Italic"),
            Cue(4, 9.5, 13.0, "Let us look at examples of timing.", speaker="NARRATOR"),
            Cue(5, 13.5, 16.0, "This one is fine.", speaker="GUEST"),
        ],
        language="en",
    )


def _overlap_track():
    return Track(
        "Overlaps",
        cues=[
            Cue(1, 0.0, 3.0, "First cue"),
            Cue(2, 2.5, 5.0, "Overlaps first"),
            Cue(3, 6.0, 8.0, "No overlap"),
            Cue(4, 7.5, 10.0, "Overlaps third"),
        ],
    )


class TestDurationBuckets:
    def test_basic(self):
        rows = duration_buckets(_track())
        assert len(rows) > 0

    def test_empty(self):
        assert isinstance(duration_buckets(Track("E")), list)


class TestDurationExtremes:
    def test_basic(self):
        rows = duration_extremes(_track())
        assert isinstance(rows, (list, dict))

    @pytest.mark.parametrize("n", [0, -1, -10])
    def test_rejects_non_positive_n(self, n):
        with pytest.raises(ValueError, match="n must be greater than zero"):
            duration_extremes(_track(), n=n)

    def test_n_limits_each_category(self):
        rows = duration_extremes(_track(), n=2)

        assert [row["category"] for row in rows].count("shortest") == 2
        assert [row["category"] for row in rows].count("longest") == 2
