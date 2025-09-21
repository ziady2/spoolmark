"""Tests for transform."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.track import Track
from subcue.transform import (
    Callable,
    Sequence,
    filter_by_duration,
    filter_cues,
    renumber_cues,
    sort_cues,
    strip_all_tags,
    strip_tags_from_track,
)


def _track():
    return Track(
        "T",
        cues=[
            Cue(1, 0, 2, "Hello world", speaker="A"),
            Cue(2, 3, 6, "Second subtitle here", speaker="B"),
            Cue(3, 7, 8, "Short one", speaker="A"),
        ],
    )


class Test_Callable:
    def test_callable(self):
        assert callable(Callable)


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_filter_by_duration:
    def test_callable(self):
        assert callable(filter_by_duration)

    def test_returns_independent_cue_copies(self):
        source = [
            Cue(1, 0, 1, "short", speaker="A", style="plain"),
            Cue(2, 2, 5, "long", speaker="B", style="note"),
        ]
        result = filter_by_duration(source, min_dur=0.5, max_dur=1.5)

        assert [cue.text for cue in result] == ["short"]
        assert result[0] is not source[0]
        result[0].text = "changed"
        assert source[0].text == "short"


class Test_filter_cues:
    def test_callable(self):
        assert callable(filter_cues)

    def test_returns_independent_cue_copies(self):
        source = _track().cues
        result = filter_cues(source, lambda cue: cue.speaker == "A")

        assert [cue.text for cue in result] == ["Hello world", "Short one"]
        assert not ({id(cue) for cue in result} & {id(cue) for cue in source})
        result[0].text = "changed"
        assert source[0].text == "Hello world"


class Test_renumber_cues:
    def test_callable(self):
        assert callable(renumber_cues)


class Test_sort_cues:
    def test_callable(self):
        assert callable(sort_cues)

    def test_sorts_independent_cue_copies(self):
        source = [
            Cue(2, 3, 4, "later", speaker="B", style="note"),
            Cue(1, 1, 2, "earlier", speaker="A", style="plain"),
        ]
        result = sort_cues(source, key="start")

        assert [cue.text for cue in result] == ["earlier", "later"]
        assert not ({id(cue) for cue in result} & {id(cue) for cue in source})
        assert (result[0].speaker, result[0].style) == ("A", "plain")
        result[0].text = "changed"
        assert source[1].text == "earlier"


class Test_strip_all_tags:
    def test_callable(self):
        assert callable(strip_all_tags)


class Test_strip_tags_from_track:
    def test_callable(self):
        assert callable(strip_tags_from_track)

    def test_replaces_cues_with_cleaned_copies(self):
        track = Track("T", cues=[Cue(1, 0, 1, "<i>Hello</i> {\\b1}world")])
        result = strip_tags_from_track(track)
        assert result[0].text == "Hello world"
        assert track[0].text == "<i>Hello</i> {\\b1}world"
