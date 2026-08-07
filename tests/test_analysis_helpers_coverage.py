"""Behavioral coverage for analysis, querying, plugins, and text helpers."""

from __future__ import annotations

import math

import pytest

from subcue.cue import Cue
from subcue.errors import DuplicateError, NotFoundError
from subcue.interpolation import (
    exponential_smoothing,
    fill_gaps,
    linear_interpolate,
    moving_average,
    resample,
    trend_direction,
)
from subcue.plugin import (
    clear,
    get_plugin,
    list_plugins,
    register,
    run_pipeline,
    run_plugin,
    unregister,
)
from subcue.query import Query
from subcue.stats import correlation, outlier_rows, percentile_table, track_stats
from subcue.text_utils import (
    char_count,
    collapse_newlines,
    escape_html,
    extract_speaker,
    join_and,
    line_count,
    normalize_whitespace,
    pad_left,
    pad_right,
    slugify,
    strip_all_tags,
    strip_ass_tags,
    strip_bom,
    strip_html_tags,
    truncate,
    word_count,
    wrap_lines,
)
from subcue.track import Track


@pytest.fixture(autouse=True)
def empty_plugin_registry():
    """Keep the process-wide plugin registry isolated from the rest of the suite."""
    clear()
    yield
    clear()


def _query_track() -> Track:
    return Track(
        "Mixed",
        cues=[
            Cue(40, 8, 10, "<i>Zulu ending</i>", speaker="BOB", style="Sign"),
            Cue(10, 0, 4, "Alpha opening", speaker="Alice", style="Dialogue"),
            Cue(30, 5, 8, "charlie middle words", speaker="", style="DIALOGUE"),
            Cue(20, 4, 5, "Bravo", speaker="ALICE", style="Note"),
        ],
        language="EN",
        created="2026-08-01",
    )


class TestInterpolationBehavior:
    def test_linear_interpolation_supports_midpoints_extrapolation_and_vertical_lines(self):
        assert linear_interpolate(0, 10, 4, 18, 1) == 12
        assert linear_interpolate(0, 10, 4, 18, 6) == 22
        assert linear_interpolate(2, 10, 2, 14, 99) == 12

    @pytest.mark.parametrize(
        ("arguments", "field"),
        [
            ((math.nan, 0, 1, 1, 0.5), "x0"),
            ((0, math.inf, 1, 1, 0.5), "y0"),
            ((0, 0, True, 1, 0.5), "x1"),
            ((0, 0, 1, "1", 0.5), "y1"),
            ((0, 0, 1, 1, None), "x"),
        ],
    )
    def test_linear_interpolation_rejects_non_finite_or_non_numeric_inputs(self, arguments, field):
        with pytest.raises(ValueError, match=field):
            linear_interpolate(*arguments)

    def test_resample_handles_empty_singleton_and_regular_series_without_mutation(self):
        source = [0, 10, 20]

        assert resample([], 4) == [0.0, 0.0, 0.0, 0.0]
        assert resample([7], 3) == [7.0, 7.0, 7.0]
        assert resample(source, 5) == [0.0, 5.0, 10.0, 15.0, 20.0]
        assert source == [0, 10, 20]

    @pytest.mark.parametrize("new_length", [0, 1, -1, 2.5, True, "3"])
    def test_resample_rejects_invalid_lengths(self, new_length):
        with pytest.raises(ValueError, match="new_length"):
            resample([1, 2], new_length)

    @pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf, True, "1"])
    def test_resample_rejects_invalid_source_values(self, bad_value):
        with pytest.raises(ValueError, match=r"values\[1\]"):
            resample([1, bad_value], 2)

    def test_moving_average_uses_smaller_edge_windows_and_accepts_large_windows(self):
        source = [0, 10, 20, 30]

        assert moving_average([], 3) == []
        assert moving_average(source, 1) == [0.0, 10.0, 20.0, 30.0]
        assert moving_average(source, 3) == [5.0, 10.0, 20.0, 25.0]
        assert moving_average(source, 4) == [10.0, 15.0, 20.0, 25.0]
        assert moving_average([2, 4], 99) == [3.0, 3.0]
        assert source == [0, 10, 20, 30]

    @pytest.mark.parametrize("window", [0, -1, 1.5, True, "2"])
    def test_moving_average_rejects_invalid_windows(self, window):
        with pytest.raises(ValueError, match="window"):
            moving_average([1, 2], window)

    def test_exponential_smoothing_applies_recurrence_and_clamps_alpha(self):
        assert exponential_smoothing([]) == []
        assert exponential_smoothing([10, 20, 30], 0.5) == [10.0, 15.0, 22.5]
        assert exponential_smoothing([0, 100], 0) == [0.0, 1.0]
        assert exponential_smoothing([0, 100], 1) == [0.0, 99.0]

    @pytest.mark.parametrize("alpha", [math.nan, math.inf, True, "0.5"])
    def test_exponential_smoothing_rejects_invalid_alpha(self, alpha):
        with pytest.raises(ValueError, match="alpha"):
            exponential_smoothing([1], alpha)

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            ([], "flat"),
            ([5], "flat"),
            ([3, 3, 3], "flat"),
            ([1, 2, 5], "rising"),
            ([5, 2, 1], "falling"),
            ([1.0, 1.0 + 1e-10], "flat"),
        ],
    )
    def test_trend_direction_classifies_least_squares_slope(self, values, expected):
        assert trend_direction(values) == expected

    def test_fill_gaps_interpolates_all_segments_and_preserves_endpoint(self):
        source_times = [0, 1, 3]
        source_values = [0, 10, 30]

        times, values = fill_gaps(source_times, source_values, 0.75)

        assert times == [0.0, 0.75, 1.5, 2.25, 3.0]
        assert values == [0.0, 7.5, 15.0, 22.5, 30.0]
        assert source_times == [0, 1, 3]
        assert source_values == [0, 10, 30]

    def test_fill_gaps_appends_an_endpoint_when_step_does_not_divide_range(self):
        times, values = fill_gaps([2, 3], [20, 30], 0.3)

        assert times == pytest.approx([2, 2.3, 2.6, 2.9, 3])
        assert values == pytest.approx([20, 23, 26, 29, 30])
        assert times[-1] == 3
        assert values[-1] == 30

    @pytest.mark.parametrize(
        ("times", "values"),
        [([], []), ([2], [9])],
    )
    def test_fill_gaps_returns_short_inputs_as_numeric_copies(self, times, values):
        result_times, result_values = fill_gaps(times, values, 1)

        assert result_times == [float(value) for value in times]
        assert result_values == [float(value) for value in values]
        assert result_times is not times
        assert result_values is not values

    @pytest.mark.parametrize(
        ("times", "values", "step", "message"),
        [
            ([0, 1], [0], 1, "equal length"),
            ([1, 1], [0, 1], 1, "strictly increasing"),
            ([2, 1], [0, 1], 1, "strictly increasing"),
            ([0, 1], [0, 1], 0, "greater than zero"),
            ([0, 1], [0, 1], -1, "greater than zero"),
            ([0, 1], [0, 1], True, "finite number"),
            ([-1e308, 1e308], [0, 1], 1, "time range must be finite"),
            ([1e16, 1e16 + 2], [0, 1], 0.1, "too small"),
            ([0, 1], [0, 1], 5e-324, "too many"),
        ],
    )
    def test_fill_gaps_rejects_invalid_shapes_order_and_steps(self, times, values, step, message):
        with pytest.raises(ValueError, match=message):
            fill_gaps(times, values, step)


class TestPluginBehavior:
    def test_registry_lifecycle_is_sorted_and_returns_the_registered_callable(self):
        upper = lambda value: value.upper()
        register("zulu", upper)
        register("alpha", str.lower)

        assert list_plugins() == ["alpha", "zulu"]
        assert get_plugin("zulu") is upper
        assert run_plugin("zulu", "mixed") == "MIXED"

        unregister("zulu")
        assert list_plugins() == ["alpha"]
        with pytest.raises(NotFoundError) as exc_info:
            get_plugin("zulu")
        assert (exc_info.value.kind, exc_info.value.identifier) == ("plugin", "zulu")

        clear()
        assert list_plugins() == []

    def test_run_plugin_forwards_keyword_arguments_and_return_value(self):
        calls = []

        def decorate(value, *, prefix, suffix):
            calls.append((value, prefix, suffix))
            return f"{prefix}{value}{suffix}"

        register("decorate", decorate)

        assert run_plugin("decorate", "cue", prefix="[", suffix="]") == "[cue]"
        assert calls == [("cue", "[", "]")]

    def test_pipeline_preserves_order_and_forwards_options_to_every_stage(self):
        calls = []

        def add(value, *, amount):
            calls.append(("add", value, amount))
            return value + amount

        def multiply(value, *, amount):
            calls.append(("multiply", value, amount))
            return value * amount

        register("multiply", multiply)
        register("add", add)

        assert run_pipeline(["add", "multiply"], 2, amount=3) == 15
        assert calls == [("add", 2, 3), ("multiply", 5, 3)]

    def test_empty_pipeline_returns_the_original_object(self):
        marker = object()

        assert run_pipeline([], marker) is marker

    def test_duplicate_and_missing_operations_preserve_registry_state(self):
        original = lambda value: value
        register("same", original)

        with pytest.raises(DuplicateError) as duplicate:
            register("same", str)
        assert (duplicate.value.kind, duplicate.value.identifier) == ("plugin", "same")
        assert get_plugin("same") is original

        with pytest.raises(NotFoundError) as missing:
            unregister("absent")
        assert (missing.value.kind, missing.value.identifier) == ("plugin", "absent")
        assert list_plugins() == ["same"]


class TestQueryBehavior:
    def test_filters_are_composable_case_insensitive_and_non_mutating(self):
        track = _query_track()
        query = (
            Query(track)
            .where_speaker("alice")
            .where_style("dialogue")
            .where_contains("OPEN")
            .where_min_duration(4)
            .where_max_duration(4)
            .where_min_cps(3)
            .where_max_cps(4)
            .where_after(0)
            .where_before(4)
            .where_min_chars(13)
            .where_max_chars(13)
            .where_has_speaker()
        )

        assert [cue.index for cue in query.execute()] == [10]
        assert [cue.index for cue in track.cues] == [40, 10, 30, 20]

    def test_generic_predicate_filter_and_empty_result_helpers(self):
        query = Query(_query_track()).where(lambda cue: cue.index > 100)

        assert query.execute() == []
        assert query.count() == 0
        assert query.first() is None
        assert query.to_rows() == []

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("start", [10, 20, 30, 40]),
            ("end", [10, 20, 30, 40]),
            ("duration", [20, 40, 30, 10]),
            ("cps", [10, 20, 40, 30]),
            ("text", [10, 20, 30, 40]),
            ("char_count", [20, 40, 10, 30]),
            ("index", [10, 20, 30, 40]),
            ("unknown-key", [10, 20, 30, 40]),
        ],
    )
    def test_supported_sort_keys_and_unknown_key_fallback(self, key, expected):
        assert [cue.index for cue in Query(_query_track()).sort_by(key).execute()] == expected

    def test_reverse_sort_offset_limit_and_first_share_execution_semantics(self):
        query = Query(_query_track()).sort_by("start", reverse=True).offset(1).limit(2)

        assert [cue.index for cue in query.execute()] == [30, 20]
        assert query.count() == 2
        assert query.first().index == 30

    def test_query_snapshots_the_track_sequence_when_created(self):
        track = _query_track()
        query = Query(track)
        track.cues.append(Cue(50, 11, 12, "Later"))

        assert query.count() == 4
        assert len(track.cues) == 5

    def test_rows_expose_cue_data_and_to_track_reindexes_while_preserving_metadata(self):
        query = Query(_query_track()).where_speaker("alice").sort_by("start", reverse=True)

        rows = query.to_rows()
        result = query.to_track("Selected")

        assert [row["index"] for row in rows] == [20, 10]
        assert (result.name, result.language, result.created) == (
            "Selected",
            "en",
            "2026-08-01",
        )
        assert [cue.index for cue in result] == [1, 2]
        assert [(cue.text, cue.speaker, cue.style) for cue in result] == [
            ("Bravo", "ALICE", "Note"),
            ("Alpha opening", "Alice", "Dialogue"),
        ]


class TestStatisticsBehavior:
    def test_track_stats_reports_empty_and_populated_tracks_with_zero_cps_excluded(self):
        empty = track_stats(Track("empty"))
        track = Track(
            "timings",
            cues=[
                Cue(1, 2, 4, "abcd"),
                Cue(2, 10, 14, "abcdefghijkl"),
                Cue(3, 7, 7, "ignored"),
            ],
        )
        populated = track_stats(track)

        assert empty == {
            "cue_count": 0,
            "total_duration": 0.0,
            "duration_mean": 0.0,
            "duration_median": 0.0,
            "duration_stdev": 0.0,
            "cps_mean": 0.0,
            "cps_median": 0.0,
        }
        assert populated["cue_count"] == 3
        assert populated["total_duration"] == 12
        assert populated["duration_mean"] == 2
        assert populated["duration_median"] == 2
        assert populated["duration_stdev"] == pytest.approx(math.sqrt(8 / 3))
        assert populated["cps_mean"] == 2.5
        assert populated["cps_median"] == 2.5

    @pytest.mark.parametrize(
        ("xs", "ys", "expected"),
        [
            ([1, 2, 3], [2, 4, 6], 1.0),
            ([1, 2, 3], [6, 4, 2], -1.0),
            ([1, 1, 1], [1, 2, 3], 0.0),
            ([1, 2, 3], [5, 5, 5], 0.0),
            ([1], [1], 0.0),
            ([], [], 0.0),
            ([1, 2], [1], 0.0),
        ],
    )
    def test_correlation_handles_direction_degenerate_data_and_shape_errors(self, xs, ys, expected):
        assert correlation(xs, ys) == pytest.approx(expected)

    def test_percentile_table_defaults_to_quintiles_and_sorts_input(self):
        values = [40, 0, 30, 10, 20]

        assert percentile_table(values) == [
            {"quantile": 0.0, "value": 0.0},
            {"quantile": 0.25, "value": 10.0},
            {"quantile": 0.5, "value": 20.0},
            {"quantile": 0.75, "value": 30.0},
            {"quantile": 1.0, "value": 40.0},
        ]
        assert values == [40, 0, 30, 10, 20]

    def test_percentile_table_accepts_custom_quantiles_and_empty_values(self):
        assert percentile_table([100, 0], [0.1, 0.5, 0.9]) == [
            {"quantile": 0.1, "value": 10.0},
            {"quantile": 0.5, "value": 50.0},
            {"quantile": 0.9, "value": 90.0},
        ]
        assert percentile_table([], [0, 1]) == [
            {"quantile": 0, "value": 0.0},
            {"quantile": 1, "value": 0.0},
        ]

    def test_outlier_rows_reports_original_indices_and_both_fence_directions(self):
        values = [10, 100, 12, -100, 11, 13]

        assert outlier_rows(values) == [
            {"index": 1, "value": 100, "fence": "high"},
            {"index": 3, "value": -100, "fence": "low"},
        ]
        assert values == [10, 100, 12, -100, 11, 13]

    def test_outlier_rows_handles_small_samples_and_configurable_factor(self):
        assert outlier_rows([1, 2, 100]) == []
        assert outlier_rows([10, 100, 12, -100, 11, 13], factor=100) == []


class TestTextHelperBehavior:
    def test_tag_stripping_handles_html_ass_combined_and_plain_text(self):
        assert strip_html_tags('<font color="red"><b>Hello</b></font>') == "Hello"
        assert strip_ass_tags(r"{\an8}{\b1}Hello{\b0}") == "Hello"
        assert strip_all_tags(r"<i>{\b1}Hello world{\b0}</i>") == "Hello world"
        assert strip_all_tags("plain") == "plain"

    def test_whitespace_bom_and_blank_line_normalization(self):
        assert normalize_whitespace(" \t alpha\t\t beta \n gamma ") == "alpha beta \n gamma"
        assert strip_bom("\ufeffhello") == "hello"
        assert strip_bom("hello\ufeff") == "hello\ufeff"
        assert strip_bom("") == ""
        assert collapse_newlines("a\n\n \t\n\nb\n\n\nc") == "a\n\nb\n\nc"
        assert collapse_newlines("") == ""

    def test_counts_ignore_tags_and_optionally_literal_spaces_and_newlines(self):
        text = "<b>Hello world</b>\n{\\i1}again{\\i0}"

        assert word_count(text) == 3
        assert char_count(text) == len("Hello world\nagain")
        assert char_count(text, exclude_spaces=True) == len("Helloworldagain")
        assert line_count("first\n \nsecond\n\t\n") == 2

    def test_truncate_covers_suffix_budget_short_text_and_trimmed_boundary(self):
        assert truncate("unchanged", 20) == "unchanged"
        assert truncate("alpha beta gamma", 10) == "alpha b..."
        assert truncate("alpha  beta gamma", 10) == "alpha..."
        assert truncate("abcdef", 2) == ".."
        assert truncate("abcdef", 3, suffix="END") == "END"

    def test_html_escaping_and_slugification_are_deterministic(self):
        assert escape_html('&<tag title="x">') == "&amp;&lt;tag title=&quot;x&quot;&gt;"
        assert slugify("  Café déjà_vu!  ") == "cafe-deja-vu"
        assert slugify("مرحبا") == ""

    def test_wrapping_keeps_words_intact_and_handles_empty_text(self):
        assert wrap_lines("one two three four", width=7) == ["one two", "three", "four"]
        assert wrap_lines("", width=3) == []
        assert wrap_lines("oversized", width=3) == ["oversized"]

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("JOHN: Hello", ("JOHN", "Hello")),
            ("DR. JANE-2: Line one\nLine two", ("DR. JANE-2", "Line one\nLine two")),
            ("john: Hello", ("", "john: Hello")),
            ("NARRATION", ("", "NARRATION")),
        ],
    )
    def test_speaker_extraction_recognizes_only_supported_uppercase_prefixes(self, text, expected):
        assert extract_speaker(text) == expected

    def test_join_and_accepts_all_cardinalities_and_general_iterables(self):
        assert join_and([]) == ""
        assert join_and(["one"]) == "one"
        assert join_and(["one", "two"]) == "one and two"
        assert join_and(item for item in ["one", "two", "three"]) == "one, two and three"

    def test_padding_adds_only_the_needed_spaces(self):
        assert pad_left("x", 3) == "  x"
        assert pad_right("x", 3) == "x  "
        assert pad_left("long", 2) == "long"
        assert pad_right("long", 2) == "long"
