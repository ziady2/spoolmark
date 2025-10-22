"""Behavioural tests for batch subtitle operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from subcue.batch import (
    SUPPORTED_FORMATS,
    BatchImportResult,
    batch_import,
    batch_stats,
    batch_validate,
    infer_format,
)
from subcue.cue import Cue
from subcue.errors import ParseError
from subcue.track import Track

SRT_TEXT = """1
00:00:01,000 --> 00:00:03,000
Hello from SRT
"""

VTT_TEXT = """WEBVTT

1
00:00:02.000 --> 00:00:04.000
Hello from VTT
"""

ASS_TEXT = """[Script Info]
Title: Batch example

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:03.00,0:00:05.00,Default,Narrator,0,0,0,,Hello from ASS
"""

TXT_TEXT = "00:00:04.000 --> 00:00:06.000 | Hello from TXT\n"


def _write(path: Path, text: str, encoding: str = "utf-8") -> Path:
    path.write_text(text, encoding=encoding)
    return path


def _clean_track(name: str = "Clean") -> Track:
    return Track(
        name,
        cues=[
            Cue(1, 0.0, 2.0, "Hello", speaker="A"),
            Cue(2, 2.2, 4.2, "World", speaker="B"),
        ],
        language="en",
    )


class TestInferFormat:
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("movie.srt", "srt"),
            ("MOVIE.VTT", "vtt"),
            ("captions.ass", "ass"),
            ("legacy.SSA", "ass"),
            ("data.json", "json"),
            ("transcript.txt", "txt"),
        ],
    )
    def test_supported_extensions(self, filename, expected):
        assert infer_format(filename) == expected

    def test_pathlike_input(self, tmp_path):
        assert infer_format(tmp_path / "movie.srt") == "srt"

    def test_no_extension_has_context(self):
        with pytest.raises(ValueError, match="no file extension"):
            infer_format("captions")

    def test_unknown_extension_has_context(self):
        with pytest.raises(ValueError, match=r"unsupported extension '.sub'"):
            infer_format("captions.sub")

    def test_invalid_path_type(self):
        with pytest.raises(TypeError, match="path-like"):
            infer_format(42)

    def test_public_formats_are_canonical_and_stable(self):
        assert SUPPORTED_FORMATS == ("ass", "json", "srt", "txt", "vtt")


class TestBatchImport:
    def test_imports_every_supported_format_in_input_order(self, tmp_path):
        json_text = json.dumps([{"index": 1, "start": 5, "end": 7, "text": "Hello from JSON"}])
        paths = [
            _write(tmp_path / "one.srt", SRT_TEXT),
            _write(tmp_path / "two.vtt", VTT_TEXT),
            _write(tmp_path / "three.ass", ASS_TEXT),
            _write(tmp_path / "four.json", json_text),
            _write(tmp_path / "five.txt", TXT_TEXT),
        ]

        result = batch_import(paths)

        assert isinstance(result, BatchImportResult)
        assert isinstance(result, list)
        assert [track.name for track in result] == [
            "one",
            "two",
            "three",
            "four",
            "five",
        ]
        assert [track[0].text for track in result] == [
            "Hello from SRT",
            "Hello from VTT",
            "Hello from ASS",
            "Hello from JSON",
            "Hello from TXT",
        ]
        assert [record["format"] for record in result.records] == [
            "srt",
            "vtt",
            "ass",
            "json",
            "txt",
        ]
        assert result.ok is True
        assert result.succeeded == 5
        assert result.failed == 0
        assert result.errors == []

    def test_ssa_extension_uses_ass_parser(self, tmp_path):
        path = _write(tmp_path / "legacy.ssa", ASS_TEXT)
        result = batch_import([path])
        assert len(result) == 1
        assert result.records[0]["format"] == "ass"

    def test_a_single_string_is_one_path_not_characters(self, tmp_path):
        path = _write(tmp_path / "single.srt", SRT_TEXT)
        result = batch_import(str(path))
        assert len(result) == 1
        assert len(result.records) == 1
        assert result[0].name == "single"

    def test_accepts_one_shot_generator(self, tmp_path):
        paths = (_write(tmp_path / f"{index}.srt", SRT_TEXT) for index in range(3))
        result = batch_import(paths)
        assert [track.name for track in result] == ["0", "1", "2"]

    def test_duplicate_paths_are_processed_independently(self, tmp_path):
        path = _write(tmp_path / "same.srt", SRT_TEXT)
        result = batch_import([path, path])
        assert len(result) == 2
        assert len(result.records) == 2
        assert result[0] is not result[1]

    def test_empty_input_is_a_successful_empty_result(self):
        result = batch_import([])
        assert result == []
        assert result.records == []
        assert result.errors == []
        assert result.ok

    def test_global_format_override_allows_unusual_extension(self, tmp_path):
        path = _write(tmp_path / "captions.payload", SRT_TEXT)
        result = batch_import([path], format=".SRT")
        assert len(result) == 1
        assert result.records[0]["format"] == "srt"

    def test_fmt_alias_accepts_long_format_name(self, tmp_path):
        path = _write(tmp_path / "captions.bin", VTT_TEXT)
        result = batch_import([path], fmt=" WebVTT ")
        assert result[0][0].text == "Hello from VTT"

    def test_equivalent_format_aliases_do_not_conflict(self, tmp_path):
        path = _write(tmp_path / "captions.bin", ASS_TEXT)
        result = batch_import([path], format="ass", fmt="ssa")
        assert len(result) == 1

    def test_conflicting_format_arguments_raise_before_reading(self, tmp_path):
        missing = tmp_path / "missing.data"
        with pytest.raises(ValueError, match="different"):
            batch_import([missing], format="srt", fmt="vtt")

    @pytest.mark.parametrize("value", ["xml", "", ".unknown"])
    def test_unknown_override_is_a_caller_error(self, value):
        with pytest.raises(ValueError, match="unsupported subtitle format"):
            batch_import([], format=value)

    def test_collects_failure_and_continues_with_later_files(self, tmp_path):
        first = _write(tmp_path / "first.srt", SRT_TEXT)
        broken = _write(tmp_path / "broken.vtt", "not webvtt")
        third = _write(tmp_path / "third.txt", TXT_TEXT)

        result = batch_import([first, broken, third])

        assert [track.name for track in result] == ["first", "third"]
        assert [record["ok"] for record in result.records] == [True, False, True]
        assert result.failed == 1
        assert result.ok is False
        error = result.errors[0]
        assert error["path"] == str(broken)
        assert error["format"] == "vtt"
        assert error["track"] is None
        assert error["error_type"] == "ParseError"
        assert "missing WEBVTT header" in error["error"]

    def test_missing_and_unsupported_files_have_per_file_errors(self, tmp_path):
        missing = tmp_path / "missing.srt"
        unsupported = _write(tmp_path / "captions.sub", "subtitle")

        result = batch_import([missing, unsupported])

        assert result == []
        assert len(result.records) == 2
        assert result.errors[0]["error_type"] == "FileNotFoundError"
        assert result.errors[0]["format"] == "srt"
        assert result.errors[1]["error_type"] == "ValueError"
        assert result.errors[1]["format"] is None

    def test_non_path_item_is_isolated_like_other_file_errors(self, tmp_path):
        good = _write(tmp_path / "good.srt", SRT_TEXT)
        result = batch_import([123, good])
        assert len(result) == 1
        assert len(result.errors) == 1
        assert result.errors[0]["path"] == "123"
        assert result.errors[0]["error_type"] == "TypeError"

    def test_optional_error_sink_receives_same_records(self, tmp_path):
        sink = []
        missing = tmp_path / "missing.srt"
        result = batch_import([missing], errors=sink)
        assert sink == result.errors
        assert sink[0] is result.errors[0]

    def test_strict_mode_raises_first_file_failure(self, tmp_path):
        good = _write(tmp_path / "good.srt", SRT_TEXT)
        broken = _write(tmp_path / "broken.srt", "invalid")
        with pytest.raises(ParseError, match="malformed or missing timing line"):
            batch_import([good, broken], strict=True)

    def test_on_error_raise_propagates_io_errors(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            batch_import([tmp_path / "missing.srt"], on_error="raise")

    def test_invalid_error_policy_is_rejected_for_empty_batches(self):
        with pytest.raises(ValueError, match="on_error"):
            batch_import([], on_error="ignore")

    @pytest.mark.parametrize("encoding", ["", "  ", None, 123])
    def test_invalid_encoding_is_rejected(self, encoding):
        with pytest.raises(ValueError, match="encoding"):
            batch_import([], encoding=encoding)

    def test_unknown_encoding_is_rejected_even_for_empty_batch(self):
        with pytest.raises(ValueError, match="unknown text encoding"):
            batch_import([], encoding="definitely-not-a-codec")

    def test_strict_must_be_boolean(self):
        with pytest.raises(TypeError, match="strict"):
            batch_import([], strict="yes")

    def test_error_sink_must_be_mutable(self):
        with pytest.raises(TypeError, match="errors"):
            batch_import([], errors=())

    def test_explicit_non_utf8_encoding(self, tmp_path):
        text = SRT_TEXT.replace("Hello from SRT", "café")
        path = _write(tmp_path / "latin.srt", text, encoding="cp1252")
        result = batch_import(path, encoding="cp1252")
        assert result[0][0].text == "café"

    def test_utf8_bom_is_consumed_by_default(self, tmp_path):
        path = _write(tmp_path / "bom.srt", "\ufeff" + SRT_TEXT)
        result = batch_import(path)
        assert result[0][0].text == "Hello from SRT"

    def test_success_records_reference_returned_track(self, tmp_path):
        path = _write(tmp_path / "movie.srt", SRT_TEXT)
        result = batch_import(path)
        record = result.records[0]
        assert record == {
            "path": str(path),
            "format": "srt",
            "ok": True,
            "track": result[0],
            "error": None,
            "error_type": None,
        }


class TestBatchStats:
    def test_returns_identifiable_detailed_stats(self):
        track = _clean_track("English")
        rows = batch_stats([track])
        assert rows[0]["name"] == "English"
        assert rows[0]["language"] == "en"
        assert rows[0]["cue_count"] == 2
        assert rows[0]["total_duration"] == 4.2
        assert rows[0]["duration_mean"] == 2.0
        assert rows[0]["cps_mean"] == 2.5

    def test_preserves_generator_order(self):
        tracks = (_clean_track(name) for name in ["Zulu", "Alpha", "Middle"])
        assert [row["name"] for row in batch_stats(tracks)] == [
            "Zulu",
            "Alpha",
            "Middle",
        ]

    def test_empty_input(self):
        assert batch_stats([]) == []

    def test_empty_track_has_zero_summary(self):
        assert batch_stats([Track("Empty")]) == [
            {
                "name": "Empty",
                "language": "",
                "cue_count": 0,
                "total_duration": 0.0,
                "duration_mean": 0.0,
                "duration_median": 0.0,
                "duration_stdev": 0.0,
                "cps_mean": 0.0,
                "cps_median": 0.0,
            }
        ]

    @pytest.mark.parametrize("value", [None, 3, "not tracks"])
    def test_bad_batch_value_raises_clear_type_error(self, value):
        with pytest.raises(TypeError, match="tracks"):
            batch_stats(value)

    def test_reports_bad_element_index(self):
        with pytest.raises(TypeError, match=r"tracks\[1\].*str"):
            batch_stats([_clean_track(), "bad"])

    def test_does_not_mutate_track_or_cues(self):
        track = _clean_track()
        original_cues = list(track.cues)
        batch_stats([track])
        assert track.cues == original_cues


class TestBatchValidate:
    def test_clean_track_has_ordered_summary(self):
        tracks = [_clean_track("One"), _clean_track("Two")]
        rows = batch_validate(tracks)
        assert [row["name"] for row in rows] == ["One", "Two"]
        assert all(row["track_name"] == row["name"] for row in rows)
        assert all(row["valid"] for row in rows)
        assert all(row["issue_count"] == 0 for row in rows)
        assert all(row["issues"] == [] for row in rows)

    def test_max_cps_is_forwarded_to_diagnostics(self):
        track = Track("Fast", cues=[Cue(1, 0, 2, "Hello")])
        assert batch_validate([track], max_cps=3)[0]["valid"] is True

        row = batch_validate([track], max_cps=2)[0]
        assert row["valid"] is False
        assert any(issue["issue_type"] == "high_cps" for issue in row["issues"])

    def test_problematic_track_keeps_detailed_issues_and_counts(self):
        track = Track(
            "Problems",
            cues=[
                Cue(1, 1.0, 1.1, "x" * 50),
                Cue(2, 1.05, 3.0, "line one\nline two\nline three"),
            ],
        )
        row = batch_validate([track])[0]
        assert row["valid"] is False
        assert row["issue_count"] == len(row["issues"])
        assert row["error_count"] + row["warning_count"] + row["info_count"] == len(row["issues"])
        assert {issue["issue_type"] for issue in row["issues"]} >= {
            "high_cps",
            "short_duration",
            "too_many_lines",
            "overlap",
        }

    def test_empty_track_is_reported_not_dropped(self):
        row = batch_validate([Track("Empty")])[0]
        assert row["cue_count"] == 0
        assert row["valid"] is False
        assert row["error_count"] == 1
        assert row["issues"][0]["issue_type"] == "empty_track"

    def test_empty_batch_returns_empty_list(self):
        assert batch_validate([]) == []

    def test_accepts_a_generator(self):
        rows = batch_validate(_clean_track(name) for name in ["A", "B"])
        assert [row["name"] for row in rows] == ["A", "B"]

    def test_does_not_mutate_track(self):
        track = _clean_track()
        before = track.to_dict()
        batch_validate([track])
        assert track.to_dict() == before

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"max_cps": 0}, "max_cps"),
            ({"max_cps": float("inf")}, "max_cps"),
            ({"min_duration": -1}, "min_duration"),
            ({"max_duration": 0}, "max_duration"),
            ({"min_gap": -0.1}, "min_gap"),
            ({"max_lines": 0}, "max_lines"),
            ({"max_chars_per_line": 0}, "max_chars_per_line"),
        ],
    )
    def test_rejects_invalid_thresholds(self, kwargs, message):
        with pytest.raises(ValueError, match=message):
            batch_validate([], **kwargs)

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"max_cps": True}, "max_cps"),
            ({"max_lines": 2.5}, "max_lines"),
            ({"max_chars_per_line": "42"}, "max_chars_per_line"),
        ],
    )
    def test_rejects_wrong_threshold_types(self, kwargs, message):
        with pytest.raises(TypeError, match=message):
            batch_validate([], **kwargs)

    def test_rejects_inverted_duration_range(self):
        with pytest.raises(ValueError, match="max_duration"):
            batch_validate([], min_duration=3, max_duration=2)

    def test_max_line_length_is_a_compatibility_alias(self):
        track = Track("Long", cues=[Cue(1, 0, 2, "123456")])
        row = batch_validate([track], max_line_length=5)[0]
        assert any(issue["issue_type"] == "long_line" for issue in row["issues"])

    def test_conflicting_line_length_options_raise(self):
        with pytest.raises(ValueError, match="different limits"):
            batch_validate([], max_chars_per_line=40, max_line_length=41)

    def test_reports_bad_track_element(self):
        with pytest.raises(TypeError, match=r"tracks\[0\].*dict"):
            batch_validate([{}])
