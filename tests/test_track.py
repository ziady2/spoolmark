"""Tests for track."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.errors import NotFoundError
from subcue.track import Track


def _cues():
    return [Cue(1, 0, 2, "A"), Cue(2, 3, 5, "B"), Cue(3, 6, 8, "C")]


class TestTrack:
    def test_basic(self):
        t = Track("Test", cues=_cues())
        assert t.name == "Test" and len(t) == 3

    def test_duration(self):
        t = Track("T", cues=_cues())
        assert t.duration == 8.0

    def test_duration_uses_time_bounds_not_input_order(self):
        cues = [Cue(2, 8, 9, "later"), Cue(1, 2, 12, "spanning")]
        assert Track("T", cues=cues).duration == 10.0

    def test_iter(self):
        t = Track("T", cues=_cues())
        assert list(t) == _cues()

    def test_getitem(self):
        t = Track("T", cues=_cues())
        assert t[0].text == "A"

    def test_sorted_cues(self):
        cues = [Cue(2, 3, 5, "B"), Cue(1, 0, 2, "A")]
        t = Track("T", cues=cues)
        assert t.sorted_cues()[0].text == "A"

    def test_reindex(self):
        t = Track("T", cues=[Cue(5, 0, 1, "x"), Cue(10, 2, 3, "y")])
        ri = t.reindex()
        assert ri[0].index == 1 and ri[1].index == 2

    def test_shift(self):
        t = Track("T", cues=_cues()).shift(1.0)
        assert t[0].start == 1.0

    def test_add_cue(self):
        t = Track("T", cues=_cues())
        t2 = t.add_cue(Cue(4, 9, 10, "D"))
        assert len(t2) == 4 and len(t) == 3

    def test_remove_cue(self):
        t = Track("T", cues=_cues())
        t2 = t.remove_cue(1)
        assert len(t2) == 2

    def test_remove_cue_does_not_share_mutable_cues(self):
        original = Track("T", cues=_cues())
        result = original.remove_cue(1)
        result[0].text = "changed"
        assert original[1].text == "B"

    def test_remove_missing_raises(self):
        with pytest.raises(NotFoundError):
            Track("T", cues=_cues()).remove_cue(99)

    def test_filter_by_speaker(self):
        cues = [Cue(1, 0, 1, "x", speaker="A"), Cue(2, 2, 3, "y", speaker="B")]
        t = Track("T", cues=cues).filter_by_speaker("A")
        assert len(t) == 1

    def test_filter_by_speaker_does_not_share_mutable_cues(self):
        original = Track("T", cues=[Cue(1, 0, 1, "x", speaker="A")])
        result = original.filter_by_speaker("a")
        result[0].text = "changed"
        assert original[0].text == "x"

    def test_overlapping_pairs(self):
        cues = [Cue(1, 0, 3, "x"), Cue(2, 2, 5, "y")]
        pairs = Track("T", cues=cues).overlapping_pairs()
        assert len(pairs) == 1

    def test_overlapping_pairs_include_nested_non_adjacent_cues(self):
        cues = [
            Cue(1, 0, 10, "outer"),
            Cue(2, 1, 2, "inner one"),
            Cue(3, 3, 4, "inner two"),
        ]
        pairs = Track("T", cues=cues).overlapping_pairs()
        assert [(left.index, right.index) for left, right in pairs] == [(1, 2), (1, 3)]

    def test_timeline_pairs_keep_furthest_covered_end(self):
        cues = [
            Cue(1, 0, 10, "outer"),
            Cue(2, 1, 2, "inner"),
            Cue(3, 12, 13, "later"),
        ]
        pairs = Track("T", cues=cues).timeline_pairs()
        assert [(left.index, right.index) for left, right in pairs] == [(1, 2), (1, 3)]

    def test_to_dict(self):
        d = Track("T", cues=_cues()).to_dict()
        assert d["name"] == "T" and len(d["cues"]) == 3

    def test_from_dict(self):
        d = Track("T", cues=_cues()).to_dict()
        t = Track.from_dict(d)
        assert len(t) == 3

    def test_copy(self):
        t = Track("T", cues=_cues())
        cp = t.copy()
        assert len(cp) == 3

    def test_summary(self):
        s = Track("T", cues=_cues()).summary()
        assert s["cue_count"] == 3
