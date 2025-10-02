"""Tests for dedup."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.dedup import Sequence, deduplicate, find_duplicates, merge_duplicates
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


class Test_deduplicate:
    def test_callable(self):
        assert callable(deduplicate)

    @pytest.mark.parametrize("operation", [find_duplicates, deduplicate, merge_duplicates])
    @pytest.mark.parametrize("fields", [(), ("missing",), "text", (1,), None, 42])
    def test_rejects_invalid_fields_before_collapsing_distinct_cues(self, operation, fields):
        cues = [Cue(1, 0, 1, "first"), Cue(2, 2, 3, "second")]

        with pytest.raises(ValueError):
            operation(cues, fields=fields)

        assert [cue.text for cue in cues] == ["first", "second"]

    def test_accepts_public_derived_cue_fields(self):
        first = Cue(1, 0, 1, "first")
        second = Cue(2, 2, 3, "second")

        assert find_duplicates([first, second], fields=("duration",)) == [[first, second]]


class Test_find_duplicates:
    def test_callable(self):
        assert callable(find_duplicates)


class Test_merge_duplicates:
    def test_callable(self):
        assert callable(merge_duplicates)
