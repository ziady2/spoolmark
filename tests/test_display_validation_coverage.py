"""Behavioral coverage for display helpers, transforms, and validation."""

from __future__ import annotations

import math

import pytest

from subcue.color import Color
from subcue.cue import Cue
from subcue.errors import TimecodeError, ValidationError
from subcue.formatter import (
    format_cps,
    format_duration,
    format_filesize,
    format_number,
    format_percentage,
    format_timecode_display,
)
from subcue.layout import Grid, Section, horizontal_rule, page_header, two_column, wrap_text
from subcue.theme import DARK, LIGHT, Theme, get_theme, register_theme
from subcue.track import Track
from subcue.transform import (
    filter_by_duration,
    filter_cues,
    renumber_cues,
    sort_cues,
    strip_tags_from_track,
    unique_speakers,
)
from subcue.validation import (
    require_non_empty,
    require_positive,
    sanitise_string,
    validate_cue_data,
    validate_timecode,
    validate_track_data,
)


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


class TestColorBehavior:
    def test_constructor_clamps_channels_and_repr_reports_values(self):
        color = Color(-0.25, 0.5, 1.75)

        assert (color.r, color.g, color.b) == (0.0, 0.5, 1.0)
        assert repr(color) == "Color(0.000, 0.500, 1.000)"

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("#1a80ff", "#1a80ff"),
            ("ABC", "#aabbcc"),
            ("000000", "#000000"),
        ],
    )
    def test_hex_round_trip_accepts_long_and_short_forms(self, raw, expected):
        assert Color.from_hex(raw).to_hex() == expected

    @pytest.mark.parametrize("raw", ["", "#12", "#12345", "#1234567", "#gggggg"])
    def test_from_hex_rejects_malformed_values(self, raw):
        with pytest.raises(ValueError):
            Color.from_hex(raw)

    def test_equality_handles_colors_and_unrelated_objects(self):
        color = Color(0.1, 0.2, 0.3)

        assert color == Color(0.1, 0.2, 0.3)
        assert color != Color(0.1, 0.2, 0.4)
        assert color != object()

    def test_lighten_and_darken_are_clamped_and_do_not_mutate_source(self):
        source = Color(0.2, 0.4, 0.6)

        assert source.lighten(-1) == source
        lighter = source.lighten(0.5)
        assert (lighter.r, lighter.g, lighter.b) == pytest.approx((0.6, 0.7, 0.8))
        assert source.lighten(2) == Color(1, 1, 1)
        assert source.darken(-1) == source
        darker = source.darken(0.5)
        assert (darker.r, darker.g, darker.b) == pytest.approx((0.1, 0.2, 0.3))
        assert source.darken(2) == Color(0, 0, 0)
        assert source == Color(0.2, 0.4, 0.6)

    def test_luminance_and_contrast_choose_readable_text(self):
        assert Color(0, 0, 0).luminance() == pytest.approx(0.0)
        assert Color(1, 1, 1).luminance() == pytest.approx(1.0)
        assert Color.from_hex("#ffffff").contrast_text() == Color(0, 0, 0)
        assert Color.from_hex("#000000").contrast_text() == Color(1, 1, 1)

    def test_gradient_includes_endpoints_and_even_intermediate_steps(self):
        start = Color(0, 0, 0)
        end = Color(1, 0.5, 0.25)

        gradient = Color.gradient(start, end, 3)

        assert gradient == [start, Color(0.5, 0.25, 0.125), end]
        assert Color.gradient(start, end, 1) == [start]
        assert Color.gradient(start, end, 0) == [start]


class TestFormatterBehavior:
    @pytest.mark.parametrize(
        ("value", "kwargs", "expected"),
        [
            (12345.678, {}, "12,345.68"),
            (-1234.5, {"precision": 1}, "-1,234.5"),
            (12345.0, {"precision": 0, "thousands_sep": "_"}, "12_345"),
            (math.nan, {}, "nan"),
            (math.inf, {}, "inf"),
            (-math.inf, {}, "-inf"),
        ],
    )
    def test_format_number_handles_grouping_precision_and_special_values(
        self, value, kwargs, expected
    ):
        assert format_number(value, **kwargs) == expected

    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (-5, "00:00"),
            (0, "00:00"),
            (59.6, "01:00"),
            (3599, "59:59"),
            (3661, "01:01:01"),
        ],
    )
    def test_format_duration_handles_bounds_rounding_and_hours(self, seconds, expected):
        assert format_duration(seconds) == expected

    def test_percentage_supports_precision_and_custom_symbol(self):
        assert format_percentage(0.856) == "85.6%"
        assert format_percentage(1.25, precision=0, symbol=" percent") == "125 percent"

    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (-0.1, "00:00:00.000"),
            (0.0014, "00:00:00.001"),
            (59.9996, "00:01:00.000"),
            (3661.2345, "01:01:01.234"),
        ],
    )
    def test_timecode_display_handles_negative_values_and_rollover(self, seconds, expected):
        assert format_timecode_display(seconds) == expected

    @pytest.mark.parametrize(
        ("value", "label"),
        [
            (-0.1, "invalid"),
            (0, "slow"),
            (15, "slow"),
            (15.1, "normal"),
            (25, "normal"),
            (25.1, "fast"),
            (35, "fast"),
            (35.1, "very fast"),
        ],
    )
    def test_cps_descriptors_cover_every_threshold(self, value, label):
        assert format_cps(value) == f"{value:.1f} cps ({label})"

    @pytest.mark.parametrize(
        ("size", "expected"),
        [
            (-1, "0 B"),
            (0, "0 B"),
            (1023, "1023 B"),
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (1024**2, "1.0 MB"),
            (1024**3, "1.0 GB"),
            (1024**4, "1.0 TB"),
        ],
    )
    def test_filesize_selects_the_expected_binary_unit(self, size, expected):
        assert format_filesize(size) == expected


class TestLayoutBehavior:
    def test_section_renders_width_limited_underline_and_repr(self):
        section = Section("Long title", "Body")

        assert section.render(width=4) == "Long title\n====\nBody"
        assert repr(section) == "Section('Long title')"

    def test_grid_clamps_dimensions_truncates_cells_and_wraps_rows(self):
        grid = Grid(columns=0, col_width=2)
        grid.add("abcdef")
        grid.add("xy")

        assert grid.columns == 1
        assert grid.col_width == 4
        assert grid.render() == "a...\nxy  "
        assert repr(grid) == "Grid(columns=1, cells=2)"

    def test_grid_renders_multiple_columns_and_partial_last_row(self):
        grid = Grid(columns=2, col_width=5)
        for value in ("A", "B", "C"):
            grid.add(value)

        assert grid.render() == "A      B    \nC    "
        assert Grid().render() == ""

    def test_horizontal_rule_uses_requested_width_and_token(self):
        assert horizontal_rule(5, "=") == "====="
        assert horizontal_rule(0) == ""

    def test_page_header_centers_title_and_optional_subtitle(self):
        assert page_header("Title", width=9) == "=========\n  Title  \n========="
        assert page_header("T", subtitle="S", width=5) == "=====\n  T  \n  S  \n====="

    def test_wrap_text_returns_plain_and_indented_multiline_text(self):
        assert wrap_text("one two three", width=7) == "one two\nthree"
        assert wrap_text("one two three", width=8, indent="> ") == "> one\n> two\n> three"

    def test_two_column_truncates_and_preserves_exact_total_width(self):
        result = two_column("abcdefgh", "12345678", total_width=11, separator="|")

        assert result == "ab...|12..."
        assert len(result) == 11


class TestThemeBehavior:
    def test_built_in_themes_are_retrievable_and_serialise_to_hex(self):
        assert get_theme("light") is LIGHT
        assert get_theme("dark") is DARK
        assert LIGHT.as_dict() == {
            "name": "light",
            "bg": "#ffffff",
            "fg": "#1a1a1a",
            "accent": "#0066cc",
            "muted": "#888888",
            "border": "#cccccc",
        }

    def test_css_variables_emits_complete_root_block(self):
        css = DARK.css_variables()

        assert css.startswith(":root {\n")
        assert "  --bg: #1e1e1e;" in css
        assert "  --fg: #d4d4d4;" in css
        assert "  --accent: #569cd6;" in css
        assert "  --muted: #808080;" in css
        assert "  --border: #333333;" in css
        assert css.endswith("\n}")
        assert repr(DARK) == "Theme('dark')"

    def test_missing_theme_lists_available_names(self):
        with pytest.raises(KeyError) as exc_info:
            get_theme("missing-display-theme")

        message = str(exc_info.value)
        assert "missing-display-theme" in message
        assert "dark, light" in message

    def test_registered_theme_is_returned_by_name(self):
        custom = Theme(
            "display-validation-coverage",
            bg=Color.from_hex("#010203"),
            fg=Color.from_hex("#fefdfc"),
            accent=Color.from_hex("#abcdef"),
            muted=Color.from_hex("#777777"),
            border=Color.from_hex("#112233"),
        )

        register_theme(custom)

        assert get_theme(custom.name) is custom
        assert custom.as_dict()["accent"] == "#abcdef"


class TestTransformBehavior:
    def test_sort_cues_obeys_key_and_direction_and_returns_copies(self):
        cues = [
            _cue(3, 3, 5, "third"),
            _cue(1, 0, 4, "first"),
            _cue(2, 2, 3, "second"),
        ]

        result = sort_cues(cues, key="end", reverse=True)

        assert [cue.text for cue in result] == ["third", "first", "second"]
        assert not ({id(cue) for cue in result} & {id(cue) for cue in cues})

    def test_filter_cues_evaluates_predicate_and_copies_matches(self):
        cues = [_cue(1, 0, 1, "A"), _cue(2, 1, 3, "B"), _cue(3, 3, 6, "C")]

        result = filter_cues(cues, lambda cue: cue.duration >= 2)

        assert [cue.text for cue in result] == ["B", "C"]
        assert all(result[index] is not cues[index + 1] for index in range(2))

    def test_strip_tags_preserves_track_and_cue_metadata_without_mutation(self):
        source = Track(
            "English",
            cues=[_cue(7, 1, 2, "<i>Hello</i> {\\b1}world", speaker="A", style="note")],
            language="EN",
            created="2026-01-02",
        )

        result = strip_tags_from_track(source)

        assert result.to_dict()["name"] == "English"
        assert result.language == "en"
        assert result.created == "2026-01-02"
        assert result[0].text == "Hello world"
        assert (result[0].index, result[0].speaker, result[0].style) == (7, "A", "note")
        assert source[0].text == "<i>Hello</i> {\\b1}world"
        assert result[0] is not source[0]

    def test_unique_speakers_skips_blanks_deduplicates_and_sorts(self):
        cues = [
            _cue(1, 0, 1, "", speaker="Zed"),
            _cue(2, 1, 2, "", speaker=""),
            _cue(3, 2, 3, "", speaker="Amy"),
            _cue(4, 3, 4, "", speaker="Zed"),
        ]

        assert unique_speakers(cues) == ["Amy", "Zed"]
        assert unique_speakers([]) == []

    def test_renumber_cues_uses_requested_start_and_preserves_sources(self):
        source = [_cue(9, 0, 1, "A"), _cue(4, 1, 2, "B")]

        result = renumber_cues(source, start=10)

        assert [cue.index for cue in result] == [10, 11]
        assert [cue.index for cue in source] == [9, 4]
        assert not ({id(cue) for cue in result} & {id(cue) for cue in source})

    def test_filter_by_duration_is_inclusive_and_returns_copies(self):
        source = [
            _cue(1, 0, 1, "short"),
            _cue(2, 1, 3, "middle"),
            _cue(3, 3, 6, "long"),
        ]

        result = filter_by_duration(source, min_dur=1, max_dur=2)

        assert [cue.text for cue in result] == ["short", "middle"]
        assert not ({id(cue) for cue in result} & {id(cue) for cue in source})
        assert filter_by_duration(source, min_dur=4, max_dur=2) == []


class TestValidationBehavior:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("00:00:01,250", 1.25), ("01:02:03.004", 3723.004), ("2.5", 2.5)],
    )
    def test_validate_timecode_returns_parsed_seconds(self, raw, expected):
        assert validate_timecode(raw) == pytest.approx(expected)

    @pytest.mark.parametrize("raw", ["not-a-time", "", None])
    def test_validate_timecode_normalises_failures_to_timecode_error(self, raw):
        with pytest.raises(TimecodeError) as exc_info:
            validate_timecode(raw)

        assert exc_info.value.raw == str(raw)

    def test_validate_cue_data_accepts_a_complete_valid_record(self):
        assert validate_cue_data({"start": 0, "end": 1.5, "text": " hello "}) == []

    @pytest.mark.parametrize("value", [None, "0", True, -1, math.nan, math.inf, -math.inf])
    def test_validate_cue_data_rejects_invalid_start_values(self, value):
        errors = validate_cue_data({"start": value, "end": 2, "text": "x"})

        assert "start must be a non-negative number" in errors

    @pytest.mark.parametrize("value", [None, "2", False, -1, math.nan, math.inf, -math.inf])
    def test_validate_cue_data_rejects_invalid_end_values(self, value):
        errors = validate_cue_data({"start": 0, "end": value, "text": "x"})

        assert "end must be a non-negative number" in errors

    @pytest.mark.parametrize("end", [0, -0.0])
    def test_validate_cue_data_requires_end_after_start(self, end):
        assert "end must be greater than start" in validate_cue_data(
            {"start": 0, "end": end, "text": "x"}
        )

    @pytest.mark.parametrize("text", [None, 123, "", "  \t\n"])
    def test_validate_cue_data_requires_non_empty_text(self, text):
        errors = validate_cue_data({"start": 0, "end": 1, "text": text})

        assert "text must be a non-empty string" in errors

    def test_validate_cue_data_reports_all_missing_fields(self):
        assert validate_cue_data({}) == [
            "start must be a non-negative number",
            "end must be a non-negative number",
            "text must be a non-empty string",
        ]

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            ({"name": "English", "cues": []}, []),
            ({"name": " ", "cues": []}, ["name must be a non-empty string"]),
            ({"name": "English", "cues": ()}, ["cues must be a list"]),
            (
                {},
                ["name must be a non-empty string", "cues must be a list"],
            ),
        ],
    )
    def test_validate_track_data_reports_shape_errors(self, data, expected):
        assert validate_track_data(data) == expected

    def test_require_non_empty_returns_trimmed_value(self):
        assert require_non_empty("  title  ", "name") == "title"

    @pytest.mark.parametrize("value", [None, 3, "", " \t\n"])
    def test_require_non_empty_rejects_non_strings_and_whitespace(self, value):
        with pytest.raises(ValidationError) as exc_info:
            require_non_empty(value, "name")

        assert exc_info.value.field == "name"
        assert "non-empty string" in exc_info.value.reason

    @pytest.mark.parametrize("value", [1, 2.5])
    def test_require_positive_returns_float_for_valid_numbers(self, value):
        result = require_positive(value, "duration")

        assert result == float(value)
        assert isinstance(result, float)

    @pytest.mark.parametrize(
        "value", [None, "1", False, True, 0, -1, math.nan, math.inf, -math.inf]
    )
    def test_require_positive_rejects_non_positive_non_numeric_and_non_finite_values(self, value):
        with pytest.raises(ValidationError) as exc_info:
            require_positive(value, "duration")

        assert exc_info.value.field == "duration"
        assert "positive number" in exc_info.value.reason

    def test_sanitise_string_removes_controls_strips_and_truncates(self):
        raw = " \x00\x07 hello\tworld\n \x1f "

        assert sanitise_string(raw) == "hello\tworld"
        assert sanitise_string("  abc  ", strip=False) == "  abc  "
        assert sanitise_string("abcdef", max_length=4) == "abcd"
        assert sanitise_string("abcdef", max_length=0) == ""
