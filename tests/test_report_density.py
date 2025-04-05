"""Tests for report_density."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.report_density import density_over_time, density_summary
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


class TestDensityOverTime:
    def test_basic(self):
        rows = density_over_time(_track())
        assert len(rows) > 0

    def test_empty(self):
        assert density_over_time(Track("E")) == []

    @pytest.mark.parametrize("interval", [0, -1, float("nan"), float("inf"), True])
    def test_rejects_invalid_interval(self, interval):
        with pytest.raises(ValueError, match="finite"):
            density_over_time(_track(), interval)

    def test_uses_full_track_end_and_union_of_overlaps(self):
        track = Track(
            "nested",
            cues=[Cue(1, 0, 10, "outer"), Cue(2, 1, 2, "inner")],
        )
        rows = density_over_time(track, interval=20)
        assert rows[0]["end_time"] == 10
        assert rows[0]["active_seconds"] == 10
        assert rows[0]["density_pct"] == 100


class TestDensitySummary:
    def test_basic(self):
        s = density_summary(_track())
        assert isinstance(s, (dict, list))
