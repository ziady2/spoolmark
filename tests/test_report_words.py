"""Tests for report_words."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.report_words import char_stats, vocabulary_summary, word_frequency
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


class TestWordFrequency:
    def test_basic(self):
        rows = word_frequency(_track())
        assert len(rows) > 0

    def test_empty(self):
        assert word_frequency(Track("E")) == []

    def test_cue_count_uses_cue_positions_not_public_indices(self):
        track = Track(
            "Duplicate indices",
            cues=[
                Cue(7, 0.0, 1.0, "Echo"),
                Cue(7, 1.0, 2.0, "echo echo"),
                Cue(8, 2.0, 3.0, "Different"),
            ],
        )

        echo = next(row for row in word_frequency(track) if row["word"] == "echo")
        assert echo["count"] == 3
        assert echo["cue_count"] == 2


class TestCharStats:
    def test_basic(self):
        rows = char_stats(_track())
        assert isinstance(rows, (list, dict))


class TestVocabularySummary:
    def test_basic(self):
        s = vocabulary_summary(_track())
        assert isinstance(s, (dict, list))
