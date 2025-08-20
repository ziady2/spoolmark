"""Tests for merge."""

from __future__ import annotations

import math

import pytest

from subcue.cue import Cue
from subcue.merge import Sequence, concatenate_tracks, interleave_tracks, merge_tracks
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


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_concatenate_tracks:
    def test_callable(self):
        assert callable(concatenate_tracks)

    def test_places_tracks_end_to_end_using_seconds(self):
        first = Track("A", cues=[Cue(1, 0, 2, "a")])
        second = Track("B", cues=[Cue(1, 10, 12, "b")])
        result = concatenate_tracks([first, second], gap=1.0)
        assert [(c.start, c.end) for c in result] == [(0.0, 2.0), (3.0, 5.0)]

    @pytest.mark.parametrize("gap", [-1, math.nan, math.inf, True])
    def test_rejects_invalid_gap_even_without_tracks(self, gap):
        with pytest.raises(ValueError, match="gap"):
            concatenate_tracks([], gap=gap)


class Test_interleave_tracks:
    def test_callable(self):
        assert callable(interleave_tracks)

    def test_contains_cues_from_both_tracks(self):
        other = Track("U", cues=[Cue(1, 1, 2, "other")])
        result = interleave_tracks(_track(), other)
        assert [c.text for c in result] == [
            "Hello world",
            "other",
            "Second subtitle here",
            "Short one",
        ]


class Test_merge_tracks:
    def test_callable(self):
        assert callable(merge_tracks)

    def test_returns_all_cues_and_requested_name(self):
        other = Track("U", cues=[Cue(1, 1, 2, "other")])
        result = merge_tracks([_track(), other], name="all")
        assert result.name == "all"
        assert len(result) == 4
        assert [c.index for c in result] == [1, 2, 3, 4]
