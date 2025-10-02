"""Behavioural coverage for rendering, conversion, and data utilities."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from subcue.ascii_renderer import (
    bar,
    box,
    horizontal_bar_chart,
    progress_bar,
    sparkline,
    table_string,
)
from subcue.binning import custom_bins, equal_width_bins, histogram_text, quantile_bins
from subcue.conversion import (
    batch_convert_srt_to_vtt,
    batch_convert_vtt_to_srt,
    fps_factor,
    framerate_convert,
    srt_to_vtt,
    vtt_to_srt,
)
from subcue.cue import Cue
from subcue.dedup import deduplicate, find_duplicates, merge_duplicates
from subcue.errors import TimecodeError
from subcue.metadata import Metadata, detect_language_hint
from subcue.search import (
    highlight_matches,
    regex_search,
    search_by_speaker,
    search_cues,
    search_track,
)
from subcue.svg_renderer import svg_bar_chart, svg_line_chart, svg_timeline
from subcue.table import TableBuilder, format_table, pivot_table, transpose
from subcue.track import Track


def _search_cues() -> list[Cue]:
    return [
        Cue(1, 0, 1, "Hello world", speaker="Alice"),
        Cue(2, 1, 2, "HELLO again: 123", speaker="ALICE COOPER"),
        Cue(3, 2, 3, "Goodbye 456"),
    ]


class TestAsciiRenderer:
    def test_bar_scales_and_clamps_values(self) -> None:
        assert bar(5, 10, width=10, char="=") == "=====" + " " * 5
        assert bar(-5, 10, width=4) == " " * 4
        assert bar(50, 10, width=4) == "####"
        assert bar(1, 0, width=4) == ""
        assert bar(1, -1, width=4) == ""
        assert bar(1, 2, width=0) == ""

    def test_sparkline_maps_range_and_handles_constant_or_empty_data(self) -> None:
        assert sparkline([], ticks="._#") == ""
        assert sparkline([0, 5, 10], ticks="._#") == "._#"
        assert sparkline([7, 7, 7], ticks="._#") == "..."

    def test_horizontal_chart_aligns_labels_and_scales_to_the_largest_value(self) -> None:
        chart = horizontal_bar_chart(["A", "Long"], [1, 2], width=4, char="=")

        assert chart.splitlines() == [
            "   A | ==   1.0",
            "Long | ==== 2.0",
        ]
        assert horizontal_bar_chart([], [1]) == ""
        assert horizontal_bar_chart(["A"], []) == ""

    def test_ascii_table_expands_columns_and_formats_extra_cells(self) -> None:
        rendered = table_string(
            ["Name", "Score"],
            [["Al", "9"], ["Beatrice", "100"]],
            padding=1,
        )
        lines = rendered.splitlines()

        assert lines[0] == " Name     | Score "
        assert lines[1] == "-" * len(lines[0])
        assert lines[2] == " Al       | 9     "
        assert lines[3] == " Beatrice | 100   "

        extra = table_string(["A"], [["x", "extra"]], padding=0)
        assert extra.splitlines()[-1] == "x|extra"

    def test_ascii_table_without_rows_still_has_header_and_separator(self) -> None:
        rendered = table_string(["Only"], [], padding=0)
        assert rendered == "Only\n----\n"

    def test_progress_bar_formats_normal_complete_and_zero_total(self) -> None:
        assert progress_bar(5, 10, width=10) == "[=====     ]  50.0%"
        assert progress_bar(20, 10, width=4, brackets=("<", ">")) == "<====> 100.0%"
        assert progress_bar(4, 0, width=3, filled_char="+", empty_char="-") == "[---]   0.0%"

    def test_progress_bar_clamps_negative_progress_to_zero(self) -> None:
        assert progress_bar(-2, 10, width=5) == "[     ]   0.0%"

    def test_box_wraps_lines_truncates_content_and_handles_empty_text(self) -> None:
        assert box("abcdefgh\nx", width=10, border="*") == (
            "**********\n* abcdef *\n* x      *\n**********"
        )
        assert box("", width=6, border="+") == "++++++\n++++++"


class TestBinning:
    def test_equal_width_bins_include_the_maximum_only_in_the_last_bin(self) -> None:
        rows = equal_width_bins([0, 1, 2, 3, 4], n_bins=2)

        assert rows == [
            {"lo": 0.0, "hi": 2.0, "count": 2},
            {"lo": 2.0, "hi": 4.0, "count": 3},
        ]
        assert sum(row["count"] for row in rows) == 5

    def test_equal_width_bins_handle_empty_invalid_and_constant_inputs(self) -> None:
        assert equal_width_bins([]) == []
        assert equal_width_bins([1, 2], n_bins=0) == []
        assert equal_width_bins([2.5, 2.5, 2.5], n_bins=8) == [{"lo": 2.5, "hi": 2.5, "count": 3}]

    def test_quantile_bins_partition_varied_data_without_losing_values(self) -> None:
        rows = quantile_bins([0, 10, 20, 30, 40], n_bins=4)

        assert rows == [
            {"lo": 0.0, "hi": 10.0, "count": 1},
            {"lo": 10.0, "hi": 20.0, "count": 1},
            {"lo": 20.0, "hi": 30.0, "count": 1},
            {"lo": 30.0, "hi": 40.0, "count": 2},
        ]
        assert sum(row["count"] for row in rows) == 5

    def test_quantile_bins_handle_empty_invalid_and_tied_inputs(self) -> None:
        assert quantile_bins([]) == []
        assert quantile_bins([1, 2], n_bins=0) == []
        assert quantile_bins([3, 3, 3], n_bins=3) == [
            {"lo": 3.0, "hi": 3.0, "count": 0},
            {"lo": 3.0, "hi": 3.0, "count": 0},
            {"lo": 3.0, "hi": 3.0, "count": 3},
        ]

    def test_custom_bins_sort_edges_apply_half_open_intervals_and_ignore_outliers(self) -> None:
        rows = custom_bins([-1, 0, 4.9, 5, 10, 11], edges=[10, 0, 5])

        assert rows == [
            {"lo": 0, "hi": 5, "count": 2},
            {"lo": 5, "hi": 10, "count": 2},
        ]
        assert custom_bins([1, 2], edges=[]) == []
        assert custom_bins([1, 2], edges=[1]) == []

    def test_histogram_renders_scaled_counts_and_no_data_message(self) -> None:
        rendered = histogram_text([0, 1, 2, 3, 4], n_bins=2, width=6, char="+")
        lines = rendered.splitlines()

        assert len(lines) == 2
        assert lines[0].endswith("++++ 2")
        assert lines[1].endswith("++++++ 3")
        assert "[    0.00,     2.00)" in lines[0]
        assert histogram_text([], n_bins=3) == "(no data)"
        assert histogram_text([1], n_bins=0) == "(no data)"


class TestConversion:
    @pytest.mark.parametrize(
        "srt,vtt",
        [
            ("00:00:01,250", "00:00:01.250"),
            ("01:02:03,004", "01:02:03.004"),
            ("00:00:00,5", "00:00:00.500"),
        ],
    )
    def test_timecode_conversion_is_bidirectional(self, srt: str, vtt: str) -> None:
        assert srt_to_vtt(srt) == vtt
        assert vtt_to_srt(vtt) == srt.replace(",5", ",500")

    @pytest.mark.parametrize("converter", [srt_to_vtt, vtt_to_srt])
    def test_timecode_conversion_rejects_invalid_input(self, converter: object) -> None:
        with pytest.raises(TimecodeError):
            converter("not-a-timecode")  # type: ignore[operator]

    def test_frame_rate_factor_and_timestamp_conversion(self) -> None:
        assert fps_factor(24, 48) == 0.5
        assert fps_factor(50, 25) == 2.0
        assert framerate_convert(10, 24, 25) == 9.6

    @pytest.mark.parametrize(
        "source,target,field",
        [
            (0, 24, "source_fps"),
            (-1, 24, "source_fps"),
            (24, 0, "target_fps"),
            (24, -1, "target_fps"),
        ],
    )
    def test_frame_rate_factor_rejects_non_positive_rates(
        self, source: float, target: float, field: str
    ) -> None:
        with pytest.raises(ValueError, match=field):
            fps_factor(source, target)

    def test_batch_srt_conversion_changes_only_well_formed_arrow_lines(self) -> None:
        source = [
            "1",
            "00:00:01,000 --> 00:00:02,500",
            "caption",
            "00:00:01.000 --> 00:00:02.000",
            "00:00:01,000 --> 00:00:02,000 --> 00:00:03,000",
        ]
        before = list(source)

        result = batch_convert_srt_to_vtt(source)

        assert result == [
            "1",
            "00:00:01.000 --> 00:00:02.500",
            "caption",
            "00:00:01.000 --> 00:00:02.000",
            "00:00:01,000 --> 00:00:02,000 --> 00:00:03,000",
        ]
        assert source == before
        assert result is not source

    def test_batch_vtt_conversion_changes_only_well_formed_arrow_lines(self) -> None:
        source = [
            "WEBVTT",
            "00:00:01.000 --> 00:00:02.500",
            "caption",
            "00:00:01,000 --> 00:00:02,000",
            "00:00:01.000 --> 00:00:02.000 --> 00:00:03.000",
        ]

        assert batch_convert_vtt_to_srt(source) == [
            "WEBVTT",
            "00:00:01,000 --> 00:00:02,500",
            "caption",
            "00:00:01,000 --> 00:00:02,000",
            "00:00:01.000 --> 00:00:02.000 --> 00:00:03.000",
        ]
        assert batch_convert_vtt_to_srt([]) == []
        assert batch_convert_srt_to_vtt([]) == []


class TestDeduplication:
    def test_find_duplicates_groups_exact_matches_in_input_order(self) -> None:
        first = Cue(1, 0, 1, "same", speaker="first")
        unique = Cue(2, 2, 3, "unique")
        duplicate = Cue(99, 0, 1, "same", speaker="second")

        groups = find_duplicates([first, unique, duplicate])

        assert groups == [[first, duplicate]]
        assert groups[0][0] is first
        assert find_duplicates([]) == []

    def test_find_duplicates_supports_custom_fields_and_numeric_tolerance(self) -> None:
        first = Cue(1, 0.0, 1.0, "same")
        near = Cue(2, 0.1, 1.1, "same")
        different_text = Cue(3, 0.1, 1.1, "other")
        too_far = Cue(4, 0.21, 1.21, "same")

        groups = find_duplicates(
            [first, near, different_text, too_far],
            tolerance=0.1,
        )

        assert groups == [[first, near]]
        assert find_duplicates([first, near], fields=("text",)) == [[first, near]]

    def test_deduplicate_keeps_first_objects_and_honours_selected_fields(self) -> None:
        first = Cue(1, 0, 1, "same")
        same_text_elsewhere = Cue(2, 2, 3, "same")
        other = Cue(3, 4, 5, "other")

        result = deduplicate([first, same_text_elsewhere, other], fields=("text",))

        assert result == [first, other]
        assert result[0] is first
        assert deduplicate([]) == []

    def test_merge_duplicates_combines_text_into_copies_without_mutating_inputs(self) -> None:
        first = Cue(1, 0, 2, "hello", speaker="A", style="Default")
        second = Cue(2, 0, 2, "bonjour", speaker="B", style="Italic")
        unique = Cue(3, 3, 4, "bye", speaker="C")

        result = merge_duplicates(
            [first, second, unique],
            fields=("start", "end"),
            separator=" | ",
        )

        assert len(result) == 2
        assert result[0].text == "hello | bonjour"
        assert (result[0].index, result[0].speaker, result[0].style) == (1, "A", "Default")
        assert result[1] == unique
        assert result[0] is not first and result[1] is not unique
        assert first.text == "hello" and second.text == "bonjour"
        assert merge_duplicates([]) == []

    def test_default_merge_requires_text_to_match(self) -> None:
        first = Cue(1, 0, 1, "same")
        duplicate = Cue(2, 0, 1, "same")
        different = Cue(3, 0, 1, "different")

        result = merge_duplicates([first, duplicate, different], separator="+")

        assert [cue.text for cue in result] == ["same+same", "different"]


class TestSvgRenderer:
    def test_empty_charts_are_valid_minimal_svg_documents(self) -> None:
        outputs = [
            svg_bar_chart([], [], width=321),
            svg_timeline([], [], width=322),
            svg_timeline([1], [], width=323),
            svg_line_chart([], width=324, height=111),
            svg_line_chart([5], width=325, height=112),
        ]

        for output in outputs:
            root = ET.fromstring(output)
            assert root.tag.endswith("svg")
            assert len(root) == 0

    def test_bar_chart_scales_bars_escapes_labels_and_sets_dimensions(self) -> None:
        output = svg_bar_chart(
            ["A&B", "B"],
            [0, 10],
            width=300,
            bar_height=10,
            gap=2,
            color="#abc",
        )
        root = ET.fromstring(output)
        rects = root.findall("{http://www.w3.org/2000/svg}rect")

        assert (root.attrib["width"], root.attrib["height"]) == ("300", "26")
        assert "A&amp;B" in output
        assert [rect.attrib["width"] for rect in rects] == ["0.0", "160.0"]
        assert [rect.attrib["y"] for rect in rects] == ["2.0", "14.0"]
        assert all(rect.attrib["fill"] == "#abc" for rect in rects)

    def test_bar_chart_never_emits_negative_rectangle_widths(self) -> None:
        root = ET.fromstring(svg_bar_chart(["loss", "gain"], [-2, 4], width=200))
        rects = root.findall("{http://www.w3.org/2000/svg}rect")

        assert all(float(rect.attrib["width"]) >= 0 for rect in rects)

    def test_all_zero_bar_values_use_zero_widths(self) -> None:
        root = ET.fromstring(svg_bar_chart(["a", "b"], [0, 0]))
        rects = root.findall("{http://www.w3.org/2000/svg}rect")
        assert [rect.attrib["width"] for rect in rects] == ["0.0", "0.0"]

    def test_timeline_positions_intervals_and_gives_zero_duration_a_visible_pixel(self) -> None:
        output = svg_timeline([0, 5], [2, 5], width=100, row_height=10, color="red")
        root = ET.fromstring(output)
        rects = root.findall("{http://www.w3.org/2000/svg}rect")

        assert (root.attrib["width"], root.attrib["height"]) == ("100", "44")
        assert [(r.attrib["x"], r.attrib["y"], r.attrib["width"]) for r in rects] == [
            ("10.0", "10.0", "32.0"),
            ("90.0", "22.0", "1.0"),
        ]
        assert all(r.attrib["fill"] == "red" for r in rects)

    def test_timeline_handles_a_zero_span(self) -> None:
        root = ET.fromstring(svg_timeline([2], [2], width=80))
        rect = root.find("{http://www.w3.org/2000/svg}rect")
        assert rect is not None
        assert (rect.attrib["x"], rect.attrib["width"]) == ("10.0", "1.0")

    def test_line_chart_maps_extrema_and_middle_value_to_expected_points(self) -> None:
        output = svg_line_chart(
            [1, 3, 2],
            width=100,
            height=50,
            color="purple",
            stroke_width=4,
        )
        root = ET.fromstring(output)
        line = root.find("{http://www.w3.org/2000/svg}polyline")

        assert line is not None
        assert line.attrib == {
            "points": "10.0,40.0 50.0,10.0 90.0,25.0",
            "fill": "none",
            "stroke": "purple",
            "stroke-width": "4",
        }

    def test_line_chart_handles_a_constant_series(self) -> None:
        root = ET.fromstring(svg_line_chart([7, 7, 7], width=100, height=50))
        line = root.find("{http://www.w3.org/2000/svg}polyline")
        assert line is not None
        assert line.attrib["points"] == "10.0,40.0 50.0,40.0 90.0,40.0"


class TestTableUtilities:
    def test_builder_expands_widths_and_applies_per_column_alignment(self) -> None:
        table = TableBuilder(["Name", "Score"])
        table.set_alignment(1, "right")
        table.set_alignment(-1, "right")
        table.set_alignment(20, "right")
        table.add_row(["A", 9])
        table.add_row(["Long name", 100])

        assert table.render().splitlines() == [
            "Name      | Score",
            "----------+------",
            "A         |     9",
            "Long name |   100",
        ]

    def test_builder_supports_short_and_extra_cells(self) -> None:
        table = TableBuilder(["A", "B"])
        table.add_row(["one"])
        table.add_row(["two", "three", "extra"])

        lines = table.render().splitlines()
        assert lines[-2] == "one"
        assert lines[-1] == "two | three | extra"

    def test_format_table_converts_values_and_handles_no_rows(self) -> None:
        rendered = format_table(["Key", "Value"], [["answer", 42], ["missing", None]])

        assert "answer  | 42" in rendered
        assert "missing | None" in rendered
        assert format_table(["A"], []) == "A\n-\n"

    def test_transpose_rectangular_empty_and_ragged_inputs(self) -> None:
        assert transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
        assert transpose([]) == []
        assert transpose([[1, 2], [3]]) == [[1, 3]]

    def test_pivot_sorts_axes_fills_missing_cells_and_uses_latest_duplicate(self) -> None:
        rows = [
            {"person": "B", "quarter": 2, "sales": 20},
            {"person": "A", "quarter": 1, "sales": 10},
            {"person": "A", "quarter": 2, "sales": 15},
            {"person": "A", "quarter": 2, "sales": 16},
            {"person": "C", "quarter": 1},
        ]

        result = pivot_table(rows, "person", "quarter", "sales")

        assert result == [
            {"person": "A", "1": 10, "2": 16},
            {"person": "B", "2": 20, "1": ""},
            {"person": "C", "1": "", "2": ""},
        ]
        assert pivot_table([], "person", "quarter", "sales") == []

    def test_pivot_requires_row_and_column_keys(self) -> None:
        with pytest.raises(KeyError):
            pivot_table([{"row": "A"}], "row", "column", "value")
        with pytest.raises(KeyError):
            pivot_table([{"column": "A"}], "row", "column", "value")


class TestMetadata:
    def test_constructor_normalises_strings_and_round_trips_all_fields(self) -> None:
        metadata = Metadata(
            title="  Movie  ",
            language=" EN-US ",
            author=" Writer ",
            source=" disc ",
            fps=23.976,
            encoding=" UTF-8 ",
            format_version=" 1.2 ",
            created=" today ",
            notes=" note ",
        )

        assert metadata.to_dict() == {
            "title": "Movie",
            "language": "en-us",
            "author": "Writer",
            "source": "disc",
            "fps": 23.976,
            "encoding": "utf-8",
            "format_version": "1.2",
            "created": "today",
            "notes": "note",
        }
        assert repr(metadata) == "Metadata(title='Movie', lang='en-us')"

    def test_from_dict_ignores_unknown_keys_and_copy_is_independent(self) -> None:
        original = Metadata.from_dict({"title": "A", "language": "FR", "unknown": 1})
        copied = original.copy()

        assert copied.to_dict() == original.to_dict()
        assert copied is not original
        copied.title = "B"
        assert original.title == "A"

    def test_default_metadata_is_empty_but_real_values_are_not(self) -> None:
        assert Metadata().is_empty()
        assert not Metadata(title="Title").is_empty()

    def test_merge_prefers_non_empty_incoming_values_and_positive_fps(self) -> None:
        base = Metadata(title="Old", language="en", fps=24, encoding="latin-1", notes="keep")
        incoming = Metadata(
            title="New",
            language="",
            fps=-1,
            encoding="",
            notes="replacement",
        )

        merged = base.merge(incoming)

        assert merged.to_dict() == {
            "title": "New",
            "language": "en",
            "author": "",
            "source": "",
            "fps": 24,
            "encoding": "latin-1",
            "format_version": "",
            "created": "",
            "notes": "replacement",
        }
        assert base.title == "Old" and incoming.title == "New"

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("plain English", "en"),
            ("hello مرحبا", "ar"),
            ("字幕", "zh"),
            ("かな", "ja"),
            ("カナ", "ja"),
            ("자막", "ko"),
            ("субтитры", "ru"),
            ("123 !?", "en"),
        ],
    )
    def test_language_hint_recognises_supported_scripts(self, text: str, expected: str) -> None:
        assert detect_language_hint(text) == expected


class TestSearch:
    def test_text_search_is_case_insensitive_by_default_and_preserves_objects(self) -> None:
        cues = _search_cues()

        result = search_cues(cues, "hello")

        assert result == cues[:2]
        assert result[0] is cues[0]
        assert search_cues(cues, "HELLO", case_sensitive=True) == [cues[1]]
        assert search_cues(cues, "missing") == []
        assert search_cues([], "anything") == []
        assert search_cues(cues, "") == cues

    def test_speaker_search_supports_exact_and_case_insensitive_partial_modes(self) -> None:
        cues = _search_cues()

        assert search_by_speaker(cues, "Alice") == [cues[0]]
        assert search_by_speaker(cues, "alice") == []
        assert search_by_speaker(cues, "ali", exact=False) == cues[:2]
        assert search_by_speaker(cues, "", exact=False) == cues[:2]
        assert search_by_speaker([], "Alice") == []

    def test_regex_search_returns_matches_and_original_cues(self) -> None:
        cues = _search_cues()

        result = regex_search(cues, r"(hello)|([0-9]+)", flags=re.IGNORECASE)

        assert [row["cue"] for row in result] == cues
        assert result[0]["matches"] == [("Hello", "")]
        assert result[1]["matches"] == [("HELLO", ""), ("", "123")]
        assert result[2]["matches"] == [("", "456")]
        assert regex_search(cues, r"not-there") == []
        with pytest.raises(re.error):
            regex_search(cues, "[")

    def test_highlight_matches_is_literal_global_and_case_preserving(self) -> None:
        assert highlight_matches("Hello hELLo", "hello") == ">>Hello<< >>hELLo<<"
        assert highlight_matches("a.b A.B", "a.b", before="[", after="]") == "[a.b] [A.B]"
        assert highlight_matches("Hello hello", "Hello", case_sensitive=True) == ">>Hello<< hello"
        assert highlight_matches("unchanged", "") == "unchanged"
        assert highlight_matches("no match", "xyz") == "no match"
        assert highlight_matches("a", "a", before=r"\1", after=r"\g<missing>") == (
            r"\1a\g<missing>"
        )

    def test_search_track_delegates_to_track_cues_and_case_option(self) -> None:
        cues = _search_cues()
        track = Track("Search", cues=cues)

        assert search_track(track, "GOODBYE") == [cues[2]]
        assert search_track(track, "Goodbye", case_sensitive=True) == [cues[2]]
        assert search_track(track, "goodbye", case_sensitive=True) == []
