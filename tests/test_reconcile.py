"""Tests for reconcile."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.reconcile import Sequence, conflict_rows, diff_tracks, field_diff, merge_tracks_by_time
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


class Test_conflict_rows:
    def test_callable(self):
        assert callable(conflict_rows)


class Test_diff_tracks:
    def test_callable(self):
        assert callable(diff_tracks)

    def test_pairs_cues_by_their_actual_index(self):
        a = Track("A", cues=[Cue(10, 0, 1, "old"), Cue(30, 3, 4, "removed")])
        b = Track("B", cues=[Cue(10, 0, 1, "new"), Cue(20, 2, 3, "added")])
        rows = diff_tracks(a, b)
        assert [(row["index"], row["status"]) for row in rows] == [
            (10, "changed"),
            (20, "added"),
            (30, "removed"),
        ]


class Test_field_diff:
    def test_callable(self):
        assert callable(field_diff)


class Test_merge_tracks_by_time:
    def test_callable(self):
        assert callable(merge_tracks_by_time)

    def test_returns_merged_reindexed_track(self):
        a = Track("A", cues=[Cue(7, 0, 1, "from a")])
        b = Track("B", cues=[Cue(9, 0.05, 1, "from b"), Cue(10, 2, 3, "extra")])
        result = merge_tracks_by_time(a, b, prefer="b")
        assert [c.text for c in result] == ["from b", "extra"]
        assert [c.index for c in result] == [1, 2]

    def test_matches_overlapping_ranges_even_when_starts_are_far_apart(self):
        a = Track("A", cues=[Cue(1, 0, 10, "long")])
        b = Track("B", cues=[Cue(2, 5, 6, "inside")])
        result = merge_tracks_by_time(a, b, tolerance=0, prefer="b")
        assert [cue.text for cue in result] == ["inside"]

    @pytest.mark.parametrize("prefer", ["", "first", "A"])
    def test_rejects_unknown_preference(self, prefer):
        with pytest.raises(ValueError, match="prefer"):
            merge_tracks_by_time(Track("A"), Track("B"), prefer=prefer)
