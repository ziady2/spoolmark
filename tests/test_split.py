"""Tests for split."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.split import split_at_gaps, split_by_speaker, split_by_style, split_by_time
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


class Test_split_at_gaps:
    def test_callable(self):
        assert callable(split_at_gaps)

    def test_nested_cue_does_not_create_false_split(self):
        track = Track(
            "nested",
            cues=[Cue(1, 0, 10, "outer"), Cue(2, 1, 2, "inner"), Cue(3, 5, 6, "inside")],
        )
        assert len(split_at_gaps(track, min_gap=2)) == 1

    def test_returns_only_cues_in_each_part(self):
        parts = split_at_gaps(_track(), min_gap=0.5)
        assert [len(part) for part in parts] == [1, 1, 1]


class Test_split_by_speaker:
    def test_callable(self):
        assert callable(split_by_speaker)

    def test_partitions_cues_instead_of_copying_whole_track(self):
        result = split_by_speaker(_track())
        assert [c.text for c in result["A"]] == ["Hello world", "Short one"]
        assert [c.text for c in result["B"]] == ["Second subtitle here"]


class Test_split_by_style:
    def test_callable(self):
        assert callable(split_by_style)

    def test_default_group_contains_only_unstyled_cues(self):
        track = Track(
            "T",
            cues=[
                Cue(1, 0, 1, "plain"),
                Cue(2, 1, 2, "styled", style="note"),
            ],
        )
        result = split_by_style(track)
        assert [c.text for c in result["(default)"]] == ["plain"]
        assert [c.text for c in result["note"]] == ["styled"]


class Test_split_by_time:
    def test_callable(self):
        assert callable(split_by_time)

    def test_partitions_by_interval(self):
        result = split_by_time(_track(), 5.0)
        assert [[c.text for c in part] for part in result] == [
            ["Hello world", "Second subtitle here"],
            ["Short one"],
        ]

    def test_skips_empty_windows_without_iterating_through_them(self):
        track = Track("late", cues=[Cue(1, 1_000_000, 1_000_001, "late")])
        parts = split_by_time(track, 0.001)
        assert len(parts) == 1
        assert parts[0][0].text == "late"

    @pytest.mark.parametrize("interval", [0, -1, float("nan"), float("inf"), True])
    def test_rejects_invalid_interval(self, interval):
        with pytest.raises(ValueError, match="finite positive"):
            split_by_time(_track(), interval)
