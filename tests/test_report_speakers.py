"""Tests for report_speakers."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.report_speakers import speaker_distribution, speaker_timing, speaker_turns
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


def _case_variant_track():
    return Track(
        "Case variants",
        cues=[
            Cue(1, 0.0, 1.0, "One", speaker="Alice"),
            Cue(2, 1.0, 3.0, "Two", speaker="alice"),
            Cue(3, 3.0, 4.0, "Three", speaker="BOB"),
            Cue(4, 4.0, 7.0, "Four", speaker="ALICE"),
            Cue(5, 7.0, 8.0, "Five", speaker="bob"),
        ],
    )


class TestSpeakerDistribution:
    def test_basic(self):
        rows = speaker_distribution(_track())
        assert len(rows) >= 2

    def test_empty(self):
        assert speaker_distribution(Track("E")) == []

    def test_groups_case_insensitively_and_keeps_first_spelling(self):
        rows = speaker_distribution(_case_variant_track())

        assert [row["speaker"] for row in rows] == ["Alice", "BOB"]
        assert [row["cue_count"] for row in rows] == [3, 2]

    def test_uses_unicode_casefolding(self):
        track = Track(
            "Unicode",
            cues=[
                Cue(1, 0.0, 1.0, "One", speaker="Stra\u00dfe"),
                Cue(2, 1.0, 2.0, "Two", speaker="STRASSE"),
            ],
        )

        assert speaker_distribution(track)[0]["speaker"] == "Stra\u00dfe"
        assert speaker_distribution(track)[0]["cue_count"] == 2


class TestSpeakerTurns:
    def test_basic(self):
        rows = speaker_turns(_track())
        assert len(rows) > 0

    def test_case_variants_do_not_start_a_new_turn(self):
        rows = speaker_turns(_case_variant_track())

        assert [row["speaker"] for row in rows] == ["Alice", "BOB", "Alice", "BOB"]
        assert [row["cue_count"] for row in rows] == [2, 1, 1, 1]

    def test_nested_cue_does_not_shorten_turn_end(self):
        track = Track(
            "Nested",
            cues=[
                Cue(1, 0.0, 10.0, "Outer", speaker="Alice"),
                Cue(2, 1.0, 2.0, "Inner", speaker="alice"),
            ],
        )

        assert speaker_turns(track)[0]["end_tc"] == "00:00:10,000"


class TestSpeakerTiming:
    def test_basic(self):
        rows = speaker_timing(_track())
        assert isinstance(rows, (list, dict))

    def test_groups_case_variants_under_first_spelling(self):
        rows = speaker_timing(_case_variant_track())

        assert [row["speaker"] for row in rows] == ["Alice", "BOB"]
        assert rows[0]["min_duration"] == 1.0
        assert rows[0]["max_duration"] == 3.0
        assert rows[0]["first_appearance_tc"] == "00:00:00,000"
        assert rows[0]["last_appearance_tc"] == "00:00:04,000"
