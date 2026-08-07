"""Tests for query."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.query import Query
from subcue.track import Track


def _track():
    return Track(
        "T",
        cues=[
            Cue(1, 0, 2, "Hello", speaker="A"),
            Cue(2, 3, 6, "World this is longer", speaker="B"),
            Cue(3, 7, 8, "Short", speaker="A"),
            Cue(4, 9, 12, "Final cue here", speaker="B"),
        ],
    )


class TestQuery:
    def test_all(self):
        assert Query(_track()).count() == 4

    def test_speaker(self):
        assert Query(_track()).where_speaker("A").count() == 2

    def test_max_duration(self):
        assert all(c.duration <= 2 for c in Query(_track()).where_max_duration(2).execute())

    def test_contains(self):
        assert Query(_track()).where_contains("hello").count() == 1

    def test_sort(self):
        cues = Query(_track()).sort_by("duration", reverse=True).execute()
        assert cues[0].duration >= cues[-1].duration

    def test_limit(self):
        assert Query(_track()).limit(2).count() == 2

    def test_offset(self):
        assert Query(_track()).offset(2).count() == 2

    def test_first(self):
        assert Query(_track()).first() is not None

    def test_first_does_not_change_later_query_results(self):
        query = Query(_track())
        assert query.first() is not None
        assert query.count() == 4

    def test_first_empty(self):
        assert Query(Track("E")).first() is None

    def test_to_rows(self):
        rows = Query(_track()).limit(1).to_rows()
        assert isinstance(rows[0], dict)

    def test_to_track(self):
        t = Query(_track()).where_speaker("A").to_track()
        assert len(t) == 2

    def test_to_track_preserves_source_metadata(self):
        source = Track(
            "T",
            cues=[Cue(1, 0, 1, "x")],
            language="ar",
            created="today",
        )
        result = Query(source).to_track()
        assert result.language == "ar"
        assert result.created == "today"

    def test_chained(self):
        assert Query(_track()).where_speaker("A").where_max_duration(2).count() >= 1
