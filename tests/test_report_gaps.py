"""Tests for report_gaps."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.report_gaps import gap_analysis, gap_summary, long_gaps
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


class TestGapAnalysis:
    def test_basic(self):
        rows = gap_analysis(_track())
        assert len(rows) > 0

    def test_empty(self):
        assert gap_analysis(Track("E")) == []

    def test_nested_cue_does_not_inflate_later_silence(self):
        track = Track(
            "nested",
            cues=[Cue(1, 0, 10, "outer"), Cue(2, 1, 2, "inner"), Cue(3, 12, 13, "later")],
        )
        rows = gap_analysis(track)
        assert rows[-1]["from_index"] == 1
        assert rows[-1]["to_index"] == 3
        assert rows[-1]["gap_seconds"] == 2


class TestGapSummary:
    def test_basic(self):
        s = gap_summary(_track())
        assert isinstance(s, (dict, list))


class TestLongGaps:
    def test_basic(self):
        rows = long_gaps(_track())
        assert isinstance(rows, list)
