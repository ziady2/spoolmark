"""Tests for search."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.search import (
    Sequence,
    highlight_matches,
    regex_search,
    search_by_speaker,
    search_cues,
    search_track,
)
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


class Test_highlight_matches:
    def test_callable(self):
        assert callable(highlight_matches)


class Test_regex_search:
    def test_callable(self):
        assert callable(regex_search)


class Test_search_by_speaker:
    def test_callable(self):
        assert callable(search_by_speaker)


class Test_search_cues:
    def test_callable(self):
        assert callable(search_cues)


class Test_search_track:
    def test_callable(self):
        assert callable(search_track)
