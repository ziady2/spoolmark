"""Tests for tooltip."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.tooltip import (
    bar_tooltip,
    cue_tooltip,
    gap_tooltip,
    pie_tooltip,
    progress_tooltip,
    speaker_tooltip,
    timeline_tooltip,
)


class TestCueTooltip:
    def test_basic(self):
        tip = cue_tooltip(Cue(1, 0, 3, "Hello", speaker="A"))
        assert "Hello" not in tip  # tooltip shows metadata not text
        assert "Speaker: A" in tip

    def test_no_speaker(self):
        tip = cue_tooltip(Cue(1, 0, 1, "x"))
        assert "Speaker" not in tip


class TestBarTooltip:
    def test_basic(self):
        tip = bar_tooltip("A", 10, 100)
        assert "A" in tip and "10" in tip
        assert "10.0%" in tip


class TestPieTooltip:
    def test_basic(self):
        tip = pie_tooltip("A", 50, 100)
        assert "50.0%" in tip


class TestTimelineTooltip:
    def test_basic(self):
        tip = timeline_tooltip(Cue(1, 0, 2, "Hello world"))
        assert "#1" in tip


class TestSpeakerTooltip:
    def test_basic(self):
        tip = speaker_tooltip("John", 10, 50)
        assert "John" in tip and "20.0%" in tip


class TestGapTooltip:
    def test_basic(self):
        tip = gap_tooltip(1, 2, 0.5)
        assert "1" in tip and "2" in tip


class TestProgressTooltip:
    def test_basic(self):
        tip = progress_tooltip(3, 10)
        assert "3/10" in tip and "30.0%" in tip
