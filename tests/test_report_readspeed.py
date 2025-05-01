"""Tests for report_readspeed."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.report_readspeed import readspeed_check, readspeed_summary
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


class TestReadspeedCheck:
    def test_basic(self):
        rows = readspeed_check(_track())
        assert len(rows) == 5

    def test_empty(self):
        assert readspeed_check(Track("E")) == []


class TestReadspeedSummary:
    def test_basic(self):
        s = readspeed_summary(_track())
        assert isinstance(s, (dict, list))
