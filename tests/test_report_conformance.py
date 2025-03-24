"""Tests for report_conformance."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.report_conformance import conformance_check, conformance_summary
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


class TestConformanceCheck:
    def test_basic(self):
        rows = conformance_check(_track())
        assert len(rows) > 0

    def test_empty(self):
        assert conformance_check(Track("E")) == []


class TestConformanceSummary:
    def test_basic(self):
        s = conformance_summary(_track())
        assert isinstance(s, (dict, list))
