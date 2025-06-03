"""Behavioural tests for the high-level diagnostic report."""

from __future__ import annotations

import json
import math

import pytest

from subcue.cue import Cue
from subcue.diagnostic import (
    SEVERITY_PENALTIES,
    health_score,
    issue_summary,
    run_diagnostics,
)
from subcue.track import Track

EXPECTED_KEYS = {
    "issue_type",
    "severity",
    "cue_index",
    "other_index",
    "timecode",
    "message",
    "value",
    "threshold",
}


def _clean_track() -> Track:
    return Track(
        "Clean",
        cues=[
            Cue(1, 0.0, 2.0, "Hello world"),
            Cue(2, 2.5, 5.0, "A tidy second cue\nwith two lines"),
        ],
    )


def _types(track: Track, **kwargs: object) -> list[str]:
    return [row["issue_type"] for row in run_diagnostics(track, **kwargs)]


class TestRunDiagnostics:
    def test_clean_track_has_no_issues_and_does_not_mutate(self) -> None:
        track = _clean_track()
        before = track.to_dict()

        assert run_diagnostics(track) == []
        assert track.to_dict() == before

    def test_empty_track_is_an_explicit_error(self) -> None:
        rows = run_diagnostics(Track("Empty"))

        assert rows == [
            {
                "issue_type": "empty_track",
                "severity": "error",
                "cue_index": None,
                "other_index": None,
                "timecode": "",
                "message": "Track contains no cues",
                "value": 0,
                "threshold": 1,
            }
        ]

    def test_duration_text_speed_and_layout_checks_have_uniform_rows(self) -> None:
        track = Track(
            "Problems",
            cues=[
                Cue(1, 0.0, 0.0, ""),
                Cue(2, 1.0, 1.5, "X" * 30),
                Cue(3, 3.0, 11.0, "one\ntwo\n" + "Y" * 43),
            ],
        )

        rows = run_diagnostics(track)
        types = [row["issue_type"] for row in rows]

        assert types == [
            "empty_text",
            "zero_duration",
            "short_duration",
            "high_cps",
            "long_duration",
            "too_many_lines",
            "long_line",
        ]
        assert all(set(row) == EXPECTED_KEYS for row in rows)
        assert json.loads(json.dumps(rows)) == rows
        high_cps = next(row for row in rows if row["issue_type"] == "high_cps")
        assert high_cps["value"] == 60.0
        assert high_cps["threshold"] == 20.0
        assert high_cps["timecode"] == "00:00:01,000"
        assert "60.00 CPS" in high_cps["message"]

    def test_values_exactly_on_every_limit_pass(self) -> None:
        track = Track(
            "Boundaries",
            cues=[
                Cue(1, 0.0, 1.0, "x" * 10),
                Cue(2, 1.25, 3.25, "12345\n67890"),
            ],
        )

        assert (
            run_diagnostics(
                track,
                max_cps=10,
                min_duration=1,
                max_duration=2,
                max_lines=2,
                max_chars_per_line=10,
                min_gap=0.25,
            )
            == []
        )

    def test_custom_thresholds_are_applied(self) -> None:
        cue = Cue(1, 0.0, 2.0, "1234567890")
        track = Track("Custom", cues=[cue])

        assert run_diagnostics(track, max_cps=5) == []
        assert _types(track, max_cps=4.9) == ["high_cps"]
        assert _types(track, min_duration=2.1) == ["short_duration"]
        assert _types(track, max_duration=1.9) == ["long_duration"]
        assert _types(track, max_lines=1, max_chars_per_line=4) == ["long_line"]

    def test_tags_do_not_count_as_visible_text_or_line_length(self) -> None:
        track = Track(
            "Markup",
            cues=[
                Cue(1, 0, 2, "<b></b>{\\i1}"),
                Cue(2, 3, 5, "<b>12345</b>"),
            ],
        )

        rows = run_diagnostics(track, max_chars_per_line=5)

        assert [row["issue_type"] for row in rows] == ["empty_text"]
        assert rows[0]["cue_index"] == 1

    def test_zero_gap_is_short_but_boundary_and_disabled_gap_pass(self) -> None:
        track = Track(
            "Gaps",
            cues=[
                Cue(1, 0, 1, "one"),
                Cue(2, 1, 2, "two"),
                Cue(3, 2.04, 3, "three"),
            ],
        )

        gaps = [row for row in run_diagnostics(track) if row["issue_type"] == "short_gap"]
        assert len(gaps) == 1
        assert gaps[0]["cue_index"] == 1
        assert gaps[0]["other_index"] == 2
        assert gaps[0]["value"] == 0
        assert not [
            row for row in run_diagnostics(track, min_gap=0) if row["issue_type"] == "short_gap"
        ]

    def test_detects_every_overlap_including_contained_cues(self) -> None:
        track = Track(
            "Nested",
            cues=[
                Cue(1, 0, 10, "long"),
                Cue(2, 1, 2, "inside one"),
                Cue(3, 3, 4, "inside two"),
            ],
        )

        overlaps = [row for row in run_diagnostics(track) if row["issue_type"] == "overlap"]

        assert [(row["cue_index"], row["other_index"]) for row in overlaps] == [(1, 2), (1, 3)]
        assert [row["value"] for row in overlaps] == [1.0, 1.0]

    def test_out_of_order_is_reported_while_pair_checks_use_chronology(self) -> None:
        track = Track(
            "Order",
            cues=[
                Cue(2, 2, 4, "later in file"),
                Cue(1, 0, 2, "earlier in time"),
            ],
        )

        rows = run_diagnostics(track)

        order = next(row for row in rows if row["issue_type"] == "out_of_order")
        assert (order["cue_index"], order["other_index"], order["value"]) == (2, 1, 2.0)
        assert [row["issue_type"] for row in rows].count("short_gap") == 1
        assert "overlap" not in _types(track)

    def test_invalid_and_duplicate_indices(self) -> None:
        first = Cue(1, 0, 1, "one")
        duplicate = Cue(1, 2, 3, "two")
        invalid = Cue(0, 4, 5, "three")
        non_integer = Cue(4, 6, 7, "four")
        non_integer.index = True

        rows = run_diagnostics(Track("Indices", cues=[first, duplicate, invalid, non_integer]))

        index_rows = [row for row in rows if "index" in row["issue_type"]]
        assert [row["issue_type"] for row in index_rows] == [
            "duplicate_index",
            "invalid_index",
            "invalid_index",
        ]
        assert index_rows[0]["other_index"] == 1
        assert index_rows[-1]["cue_index"] is None

    @pytest.mark.parametrize(
        "start,end",
        [
            (float("nan"), 2.0),
            (0.0, float("inf")),
            (-1.0, 1.0),
            (2.0, 1.0),
            (True, 1.0),
        ],
    )
    def test_mutated_invalid_timing_is_reported_without_crashing(
        self, start: float, end: float
    ) -> None:
        cue = Cue(1, 0, 1, "text")
        cue.start = start
        cue.end = end

        rows = run_diagnostics(Track("Bad timing", cues=[cue]))

        assert [row["issue_type"] for row in rows] == ["invalid_timing"]
        assert rows[0]["timecode"] == ""

    def test_non_string_mutated_text_is_treated_as_empty(self) -> None:
        cue = Cue(1, 0, 2, "text")
        cue.text = None  # type: ignore[assignment]

        rows = run_diagnostics(Track("Bad text", cues=[cue]))

        assert _types(Track("Bad text", cues=[cue])) == ["empty_text"]
        assert rows[0]["message"] == "Cue has no visible text"

    def test_rejects_wrong_track_or_cue_types(self) -> None:
        with pytest.raises(TypeError, match="track must be a Track"):
            run_diagnostics(object())  # type: ignore[arg-type]

        track = Track("Bad cue")
        track.cues.append(object())  # type: ignore[arg-type]
        with pytest.raises(TypeError, match=r"track\.cues\[0\] must be a Cue"):
            run_diagnostics(track)

    @pytest.mark.parametrize(
        "kwargs, message",
        [
            ({"max_cps": 0}, "max_cps must be greater than zero"),
            ({"max_cps": math.nan}, "max_cps must be a finite number"),
            ({"max_cps": True}, "max_cps must be a finite number"),
            ({"min_duration": -0.1}, "min_duration must be non-negative"),
            ({"max_duration": 0}, "max_duration must be greater than zero"),
            ({"min_duration": 3, "max_duration": 2}, "max_duration must be greater"),
            ({"max_lines": 0}, "max_lines must be a positive integer"),
            ({"max_lines": 1.5}, "max_lines must be a positive integer"),
            (
                {"max_chars_per_line": False},
                "max_chars_per_line must be a positive integer",
            ),
            ({"min_gap": -1}, "min_gap must be non-negative"),
        ],
    )
    def test_invalid_settings_raise_value_error(
        self, kwargs: dict[str, object], message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            run_diagnostics(_clean_track(), **kwargs)


class TestHealthScore:
    def test_clean_score_has_documented_shape(self) -> None:
        assert health_score(_clean_track()) == {
            "score": 100.0,
            "total_issues": 0,
            "errors": 0,
            "warnings": 0,
            "info": 0,
            "deductions": 0,
        }

    def test_empty_track_scores_zero(self) -> None:
        assert health_score(Track("Empty")) == {
            "score": 0.0,
            "total_issues": 1,
            "errors": 1,
            "warnings": 0,
            "info": 0,
            "deductions": 100.0,
        }

    def test_score_counts_severities_and_uses_public_penalties(self) -> None:
        track = Track(
            "Mixed",
            cues=[
                Cue(1, 0.0, 0.5, "short"),
                Cue(2, 0.4, 1.4, "normal"),
                Cue(3, 1.41, 3.0, "normal"),
            ],
        )
        issues = run_diagnostics(track)
        score = health_score(track)
        expected = sum(SEVERITY_PENALTIES[row["severity"]] for row in issues)

        assert (score["errors"], score["warnings"], score["info"]) == (1, 1, 1)
        assert score["total_issues"] == 3
        assert score["deductions"] == expected == 21.0
        assert score["score"] == 79.0

    def test_score_and_deduction_are_clamped(self) -> None:
        cues = [Cue(i + 1, 0, 0, "") for i in range(5)]

        score = health_score(Track("Very broken", cues=cues))

        assert score["deductions"] == 100.0
        assert score["score"] == 0.0

    def test_custom_thresholds_flow_through(self) -> None:
        track = Track("CPS", cues=[Cue(1, 0, 2, "1234567890")])

        assert health_score(track, max_cps=4.9)["warnings"] == 1
        assert health_score(track, max_cps=5)["warnings"] == 0


class TestIssueSummary:
    def test_clean_summary_is_empty(self) -> None:
        assert issue_summary(_clean_track()) == []

    def test_groups_counts_and_sorts_by_severity_then_name(self) -> None:
        track = Track(
            "Summary",
            cues=[
                Cue(1, 0.0, 0.5, "A" * 30),
                Cue(2, 0.4, 0.9, "B" * 30),
                Cue(3, 0.91, 2.0, "fine"),
            ],
        )

        rows = issue_summary(track)

        assert rows == [
            {"issue_type": "overlap", "count": 1, "severity": "error"},
            {"issue_type": "high_cps", "count": 2, "severity": "warning"},
            {"issue_type": "short_duration", "count": 2, "severity": "warning"},
            {"issue_type": "short_gap", "count": 1, "severity": "info"},
        ]

    def test_custom_thresholds_flow_through(self) -> None:
        track = Track("Summary", cues=[Cue(1, 0, 2, "1234567890")])

        assert issue_summary(track, max_cps=4.9) == [
            {"issue_type": "high_cps", "count": 1, "severity": "warning"}
        ]
