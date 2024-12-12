"""Tests for report_timing."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.report_timing import timing_per_cue, timing_quartiles, timing_summary
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


class TestTimingPerCue:
    def test_basic(self):
        rows = timing_per_cue(_track())
        assert len(rows) == 5

    def test_has_keys(self):
        rows = timing_per_cue(_track())
        assert isinstance(rows[0], dict)

    def test_empty(self):
        assert timing_per_cue(Track("E")) == []


class TestTimingSummary:
    def test_basic(self):
        s = timing_summary(_track())
        assert isinstance(s, (dict, list))


class TestTimingQuartiles:
    def test_basic(self):
        rows = timing_quartiles(_track())
        assert isinstance(rows, (list, dict))
