"""Behavioral coverage for wrapping, reconciliation, and timing reports."""

from __future__ import annotations

import math
import re

import pytest

from subcue.cue import Cue
from subcue.reconcile import conflict_rows, diff_tracks, field_diff, merge_tracks_by_time
from subcue.report_cps import cps_outliers, cps_per_cue, cps_summary
from subcue.report_gaps import gap_analysis, gap_summary, long_gaps
from subcue.report_readspeed import readspeed_check, readspeed_summary
from subcue.report_sync import sync_issues, sync_summary
from subcue.report_timing import timing_per_cue, timing_quartiles, timing_summary
from subcue.track import Track
from subcue.wordwrap import balance_score, check_line_lengths, rebalance_lines, wrap_subtitle


def _cue(
    index: int,
    start: float,
    end: float,
    text: str,
    *,
    speaker: str = "",
    style: str = "",
) -> Cue:
    return Cue(index, start, end, text, speaker=speaker, style=style)


def _track(name: str, *cues: Cue) -> Track:
    return Track(name, cues=list(cues), language="en", created="2026-01-02")


def _visible_words(text: str) -> list[str]:
    without_html = re.sub(r"<[^>]*>", "", text)
    without_markup = re.sub(r"\{[^}]*\}", "", without_html)
    return without_markup.split()


class TestMarkupAwareWrapping:
    def test_whitespace_only_overflow_is_returned_losslessly(self):
        original = "\n\n"

        assert wrap_subtitle(original, max_width=4, max_lines=1) == original

    def test_malformed_html_delimiter_is_visible_text_not_swallowed_markup(self):
        original = "one <broken two three"

        result = wrap_subtitle(original, max_width=10, max_lines=2)

        assert result.replace("\n", " ") == original
        assert "<broken" in result

    @pytest.mark.parametrize("tag", ["<!note>", "<?cue>", "<123>"])
    def test_non_element_html_like_tokens_are_preserved(self, tag):
        original = f"{tag}one two three four"

        result = wrap_subtitle(original, max_width=9, max_lines=2)

        assert tag in result
        assert _visible_words(result) == ["one", "two", "three", "four"]

    def test_void_and_self_closing_tags_are_not_synthesised_across_lines(self):
        original = "one<br> two<hr/> three four"

        result = wrap_subtitle(original, max_width=9, max_lines=2)

        assert result.count("<br>") == 1
        assert result.count("<hr/>") == 1
        assert "</br>" not in result
        assert "</hr>" not in result
        assert _visible_words(result) == ["one", "two", "three", "four"]

    def test_tags_separated_by_whitespace_remain_attached_to_visible_words(self):
        original = "<i> one two three four </i>"

        result = wrap_subtitle(original, max_width=10, max_lines=2)

        assert _visible_words(result) == ["one", "two", "three", "four"]
        assert result.count("<i>") >= 1
        assert result.count("</i>") >= 1

    def test_tag_only_input_does_not_create_visible_content(self):
        result = wrap_subtitle("<i>\n\n", max_width=5, max_lines=1)

        assert _visible_words(result) == []
        assert len(result.splitlines()) <= 1

    def test_overlong_first_word_gets_its_own_line_without_truncation(self):
        original = "extraordinary tiny tail"

        result = wrap_subtitle(original, max_width=5, max_lines=3)

        assert result.splitlines()[0] == "extraordinary"
        assert _visible_words(result) == original.split()
        assert len(result.splitlines()) == 3

    def test_check_line_lengths_counts_visible_text_around_malformed_markup(self):
        report = check_line_lengths("<broken text", max_width=5, max_lines=1)

        assert report == {
            "conformant": False,
            "line_count": 1,
            "max_line_length": 12,
            "issues": ["line 1 too long: 12 > 5"],
        }

    @pytest.mark.parametrize("function", [check_line_lengths, balance_score, rebalance_lines])
    def test_all_wrapping_entry_points_reject_non_string_text(self, function):
        with pytest.raises(TypeError, match="text must be a string"):
            function(None)  # type: ignore[arg-type]

    @pytest.mark.parametrize("width", [0, -1, 1.5, True])
    def test_rebalance_rejects_invalid_width(self, width):
        with pytest.raises(ValueError, match="max_width"):
            rebalance_lines("one two", max_width=width)  # type: ignore[arg-type]

    def test_rebalance_preserves_ass_and_html_markup_with_visible_words(self):
        original = '<font color="bright red">{\\i1}one two\nthree four{\\i0}</font>'

        result = rebalance_lines(original, max_width=10)

        assert 'color="bright red"' in result
        assert result.count(r"{\i1}") == 1
        assert result.count(r"{\i0}") == 1
        assert _visible_words(result) == ["one", "two", "three", "four"]


class TestReconciliationBehavior:
    def test_field_diff_reports_only_requested_changed_fields(self):
        before = _cue(1, 0, 1, "old", speaker="A", style="plain")
        after = _cue(1, 0.1, 1, "new", speaker="B", style="plain")

        assert field_diff(before, after, fields=("text", "speaker", "style")) == {
            "text": ("old", "new"),
            "speaker": ("A", "B"),
        }
        assert field_diff(before, before.copy()) == {}

    def test_diff_tracks_reports_changed_added_and_removed_in_index_order(self):
        before = _track(
            "before",
            _cue(30, 3, 4, "removed"),
            _cue(10, 0, 1, "old", speaker="A"),
        )
        after = _track(
            "after",
            _cue(20, 2, 3, "added"),
            _cue(10, 0, 1, "new", speaker="A"),
        )

        rows = diff_tracks(before, after, fields=("text",))

        assert rows == [
            {"index": 10, "status": "changed", "diffs": {"text": ("old", "new")}},
            {"index": 20, "status": "added", "diffs": {}},
            {"index": 30, "status": "removed", "diffs": {}},
        ]

    def test_diff_tracks_omits_equal_cues(self):
        cue = _cue(1, 0, 1, "same", speaker="A")

        assert diff_tracks(_track("a", cue), _track("b", cue.copy())) == []

    def test_merge_keeps_unmatched_cues_and_preferred_matches_as_copies(self):
        from_a = _cue(7, 0, 1, "A match", speaker="A", style="a")
        unmatched_a = _cue(8, 5, 6, "A only", speaker="A")
        from_b = _cue(9, 0.05, 1.05, "B match", speaker="B", style="b")
        unmatched_b = _cue(10, 3, 4, "B only", speaker="B")
        track_a = _track("Primary", from_a, unmatched_a)
        track_b = _track("Secondary", from_b, unmatched_b)

        result = merge_tracks_by_time(track_a, track_b, tolerance=0.1, prefer="a")

        assert [cue.text for cue in result] == ["A match", "B only", "A only"]
        assert [cue.index for cue in result] == [1, 2, 3]
        assert (result.name, result.language, result.created) == ("Primary", "en", "2026-01-02")
        assert not (
            {id(cue) for cue in result} & {id(from_a), id(unmatched_a), id(from_b), id(unmatched_b)}
        )

    def test_merge_selects_nearest_unused_candidate_and_honours_prefer_b(self):
        track_a = _track("A", _cue(1, 1.0, 2.0, "target"), _cue(2, 1.1, 2.1, "second"))
        track_b = _track(
            "B",
            _cue(3, 0.8, 2.0, "far"),
            _cue(4, 1.02, 2.02, "near"),
        )

        result = merge_tracks_by_time(track_a, track_b, tolerance=0, prefer="b")

        assert [cue.text for cue in result] == ["far", "near"]

    def test_conflict_rows_reports_only_matching_ranges_with_different_text(self):
        track_a = _track("A", _cue(1, 1, 2, "alpha"), _cue(2, 10, 11, "same"))
        track_b = _track(
            "B",
            _cue(3, 2.05, 3, "beta"),
            _cue(4, 10, 11, "same"),
            _cue(5, 20, 21, "distant"),
        )

        assert conflict_rows(track_a, track_b, tolerance=0.05) == [
            {
                "start": 1.0,
                "text_a": "alpha",
                "text_b": "beta",
                "time_diff": pytest.approx(1.05),
            }
        ]

    @pytest.mark.parametrize("tolerance", [-0.1, math.nan, math.inf, True, "0.1", None])
    def test_reconciliation_rejects_invalid_tolerances(self, tolerance):
        with pytest.raises(ValueError, match="tolerance"):
            conflict_rows(Track("A"), Track("B"), tolerance=tolerance)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="tolerance"):
            merge_tracks_by_time(Track("A"), Track("B"), tolerance=tolerance)  # type: ignore[arg-type]

    @pytest.mark.parametrize("prefer", ["", "A", "first", None])
    def test_merge_rejects_invalid_preference(self, prefer):
        with pytest.raises(ValueError, match="prefer"):
            merge_tracks_by_time(Track("A"), Track("B"), prefer=prefer)  # type: ignore[arg-type]


class TestSyncReportBehavior:
    def test_sync_issues_describes_every_supported_problem(self):
        track = _track(
            "broken",
            _cue(1, 1.0, 2.0, "first"),
            _cue(2, 0.0, 0.2, "short"),
            _cue(3, 1.8, 3.0, "overlap"),
            _cue(4, 3.02, 4.0, "short gap"),
        )

        rows = sync_issues(track)
        by_type = {row["issue_type"]: row for row in rows}

        assert set(by_type) == {"short_cue", "overlap", "short_gap", "order"}
        assert by_type["short_cue"] == {
            "issue_type": "short_cue",
            "severity": "warning",
            "cue_index": 2,
            "other_index": None,
            "timecode": "00:00:00,000",
            "detail": "Cue duration 0.200s < 0.3s",
            "value": 0.2,
        }
        assert by_type["overlap"]["severity"] == "error"
        assert by_type["overlap"]["value"] == pytest.approx(0.2)
        assert by_type["short_gap"]["value"] == pytest.approx(0.02)
        assert by_type["order"]["value"] == pytest.approx(1.0)

    def test_sync_summary_counts_severities_and_clamps_bad_health_to_zero(self):
        track = _track(
            "broken",
            _cue(1, 1.0, 2.0, "first"),
            _cue(2, 0.0, 0.2, "short"),
            _cue(3, 1.8, 3.0, "overlap"),
            _cue(4, 3.02, 4.0, "short gap"),
        )

        assert sync_summary(track) == [
            {
                "track_name": "broken",
                "total_cues": 4,
                "total_issues": 4,
                "error_count": 2,
                "warning_count": 2,
                "overlap_count": 1,
                "short_gap_count": 1,
                "short_cue_count": 1,
                "order_count": 1,
                "health_score": 0.0,
            }
        ]

    def test_sync_summary_empty_track_is_healthy(self):
        assert sync_summary(Track("empty")) == [
            {
                "track_name": "empty",
                "total_cues": 0,
                "total_issues": 0,
                "error_count": 0,
                "warning_count": 0,
                "overlap_count": 0,
                "short_gap_count": 0,
                "short_cue_count": 0,
                "order_count": 0,
                "health_score": 100.0,
            }
        ]


class TestCpsAndGapReportEdges:
    def test_cps_report_covers_ok_warning_and_error_thresholds_in_time_order(self):
        track = _track(
            "speeds",
            _cue(3, 2, 3, "x" * 30),
            _cue(1, 0, 1, "abc"),
            _cue(2, 1, 2, "x" * 20),
        )

        rows = cps_per_cue(track)

        assert [row["index"] for row in rows] == [1, 2, 3]
        assert [row["rating"] for row in rows] == ["ok", "warn", "error"]
        assert rows[2]["text_preview"] == "x" * 30
        assert cps_summary(track)[0]["warn_count"] == 2
        assert cps_summary(track)[0]["error_count"] == 1

    def test_empty_cps_summary_has_stable_zero_shape(self):
        summary = cps_summary(Track("empty"))[0]

        assert summary == {
            "track_name": "empty",
            "cue_count": 0,
            "avg_cps": 0.0,
            "median_cps": 0.0,
            "min_cps": 0.0,
            "max_cps": 0.0,
            "stdev_cps": 0.0,
            "p90_cps": 0.0,
            "warn_count": 0,
            "error_count": 0,
        }

    def test_cps_outliers_are_strictly_above_threshold_with_excess(self):
        track = _track("speeds", _cue(1, 0, 1, "x" * 10), _cue(2, 2, 3, "x" * 11))

        rows = cps_outliers(track, threshold=10)

        assert len(rows) == 1
        assert rows[0]["index"] == 2
        assert rows[0]["cps"] == 11.0
        assert rows[0]["excess"] == 1.0

    def test_gap_reports_distinguish_overlap_touching_and_positive_silence(self):
        track = _track(
            "gaps",
            _cue(1, 0, 2, "one"),
            _cue(2, 1.5, 3, "overlap"),
            _cue(3, 3, 4, "touch"),
            _cue(4, 10, 11, "long gap"),
        )

        rows = gap_analysis(track)
        summary = gap_summary(track)[0]

        assert [row["gap_seconds"] for row in rows] == [-0.5, 0.0, 6.0]
        assert [row["is_overlap"] for row in rows] == [True, False, False]
        assert rows[0]["gap_human"] == "0s"
        assert (summary["negative_count"], summary["zero_count"], summary["positive_count"]) == (
            1,
            1,
            1,
        )

    def test_empty_gap_summary_and_long_gap_excess_have_stable_shapes(self):
        assert gap_summary(Track("empty"))[0]["pair_count"] == 0
        track = _track("gaps", _cue(1, 0, 1, "one"), _cue(2, 7, 8, "two"))

        assert long_gaps(track, threshold=5) == [
            {
                "from_index": 1,
                "to_index": 2,
                "gap_seconds": 6.0,
                "excess": 1.0,
                "from_end_tc": "00:00:01,000",
                "to_start_tc": "00:00:07,000",
            }
        ]

    @pytest.mark.parametrize("threshold", [-1, math.nan, math.inf, True, "5", None])
    def test_long_gaps_rejects_invalid_thresholds(self, threshold):
        with pytest.raises(ValueError, match="threshold"):
            long_gaps(Track("empty"), threshold=threshold)  # type: ignore[arg-type]


class TestReadspeedAndTimingReportEdges:
    def test_readspeed_reports_independent_failure_reasons(self):
        track = _track(
            "reading",
            _cue(1, 0, 2, "one two"),
            _cue(2, 3, 4, "x" * 30),
            _cue(3, 5, 6, "a b c d"),
            _cue(4, 7, 7.5, "a"),
        )

        rows = readspeed_check(track)
        summary = readspeed_summary(track)[0]

        assert [row["pass_all"] for row in rows] == [True, False, False, False]
        assert rows[1]["cps_ok"] is False
        assert rows[2]["wps_ok"] is False
        assert rows[3]["duration_ok"] is False
        assert summary["pass_count"] == 1
        assert summary["fail_count"] == 3
        assert summary["pass_rate"] == 25.0
        assert summary["cps_fail_count"] == 1
        assert summary["wps_fail_count"] == 1
        assert summary["duration_fail_count"] == 1

    def test_empty_readspeed_summary_has_stable_zero_shape(self):
        assert readspeed_summary(Track("empty")) == [
            {
                "track_name": "empty",
                "cue_count": 0,
                "pass_count": 0,
                "fail_count": 0,
                "pass_rate": 0.0,
                "cps_fail_count": 0,
                "wps_fail_count": 0,
                "duration_fail_count": 0,
                "avg_cps": 0.0,
                "avg_wps": 0.0,
                "p95_cps": 0.0,
            }
        ]

    def test_timing_summary_and_quartiles_report_exact_distribution(self):
        track = _track(
            "timing",
            _cue(1, 0, 1, "one"),
            _cue(2, 2, 4, "two"),
            _cue(3, 5, 8, "three"),
            _cue(4, 9, 13, "four"),
        )

        summary = timing_summary(track)[0]
        quartiles = timing_quartiles(track)

        assert summary["cue_count"] == 4
        assert summary["total_duration"] == 13.0
        assert summary["avg_duration"] == 2.5
        assert [row["quartile"] for row in quartiles] == ["Q1", "Q2", "Q3", "Q4"]
        assert [row["count"] for row in quartiles] == [1, 1, 1, 1]
        assert [row["pct"] for row in quartiles] == [25.0, 25.0, 25.0, 25.0]

    def test_empty_timing_reports_and_zero_duration_percentages_are_defined(self):
        assert timing_summary(Track("empty"))[0]["cue_count"] == 0
        assert timing_quartiles(Track("empty")) == []
        zero = _track("zero", _cue(1, 2, 2, "instant"))

        assert timing_per_cue(zero)[0]["pct_of_total"] == 0.0
