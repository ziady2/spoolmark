"""Tests for report_summary."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.report_summary import full_summary, quality_breakdown, summary_rows
from subcue.track import Track


def _track():
    return Track(
        "T",
        cues=[
            Cue(1, 0, 3, "Hello world", speaker="A"),
            Cue(2, 4, 7, "Second subtitle", speaker="B"),
            Cue(3, 8, 9, "Short one", speaker="A"),
        ],
    )


class TestFullSummary:
    def test_basic(self):
        s = full_summary(_track())
        assert s["cue_count"] == 3
        assert "timing" in s
        assert "cps" in s

    def test_empty(self):
        s = full_summary(Track("E"))
        assert s["cue_count"] == 0

    def test_empty_has_the_same_schema_as_non_empty(self):
        empty = full_summary(Track("E"))
        populated = full_summary(_track())
        assert empty.keys() == populated.keys()
        for section in ("timing", "cps", "speakers", "quality"):
            assert empty[section].keys() == populated[section].keys()


class TestSummaryRows:
    def test_basic(self):
        rows = summary_rows([_track()])
        assert len(rows) == 1
        assert "quality_score" in rows[0]


class TestQualityBreakdown:
    def test_basic(self):
        rows = quality_breakdown(_track())
        assert len(rows) > 0
        assert "check" in rows[0]

    def test_empty(self):
        assert quality_breakdown(Track("E")) == []

    def test_overlap_score_never_becomes_negative(self):
        track = Track("dense", cues=[Cue(i, 0, 1, str(i)) for i in range(1, 5)])
        overlap_check = quality_breakdown(track)[-1]
        assert overlap_check == {
            "check": "No overlaps",
            "passed": 0,
            "total": 4,
            "score": 0.0,
        }
