"""Behavioral tests for high-level subtitle file I/O."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from subcue.cue import Cue
from subcue.errors import FormatError, ParseError
from subcue.io import (
    INPUT_FORMATS,
    OUTPUT_FORMATS,
    cues_to_ass,
    decode_subtitle_bytes,
    detect_format,
    format_from_path,
    load_track,
    normalize_format,
    parse_track,
    serialize_track,
    suggested_output_path,
    write_track,
)
from subcue.track import Track

SRT = """1
00:00:01,000 --> 00:00:03,500
Hello, world!

2
00:00:04,000 --> 00:00:06,000
Second line
"""

VTT = """WEBVTT

1
00:00:01.000 --> 00:00:03.500
Hello, world!
"""

ASS = r"""[Script Info]
Title: Test
ScriptType: v4.00+

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.50,Default,Alice,0,0,0,,Hello\Nworld
"""

TXT = """00:00:01.000 --> 00:00:03.500 | Hello
00:00:04.000 --> 00:00:06.000 | World
"""


@pytest.fixture
def track() -> Track:
    return Track(
        "Demo",
        language="en",
        cues=[
            Cue(1, 1.0, 3.5, "Hello, world!", speaker="Alice"),
            Cue(2, 4.0, 6.0, "Second\nline", style="Caption"),
        ],
    )


class TestNormalizeFormat:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("SRT", "srt"),
            (".vtt", "vtt"),
            ("SubRip", "srt"),
            ("webvtt", "vtt"),
            ("ssa", "ass"),
            ("text", "txt"),
        ],
    )
    def test_input_names_and_aliases(self, raw: str, expected: str) -> None:
        assert normalize_format(raw) == expected

    @pytest.mark.parametrize("value", ["", "csv", "html", "unknown"])
    def test_rejects_unsupported_input(self, value: str) -> None:
        with pytest.raises(FormatError, match="unsupported input format"):
            normalize_format(value)

    def test_output_accepts_render_only_formats(self) -> None:
        assert normalize_format("htm", for_output=True) == "html"
        assert normalize_format("CSV", for_output=True) == "csv"

    def test_declared_format_lists_are_stable(self) -> None:
        assert INPUT_FORMATS == ("srt", "vtt", "ass", "json", "txt")
        assert OUTPUT_FORMATS[-2:] == ("csv", "html")


class TestFormatDetection:
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("captions.SRT", "srt"),
            ("captions.vtt", "vtt"),
            ("captions.ssa", "ass"),
            ("captions.text", "txt"),
            ("captions.json", "json"),
        ],
    )
    def test_format_from_path(self, filename: str, expected: str) -> None:
        assert format_from_path(filename) == expected

    def test_output_only_extension_requires_output_mode(self) -> None:
        with pytest.raises(FormatError, match="unsupported input format"):
            format_from_path("report.csv")
        assert format_from_path("report.csv", for_output=True) == "csv"

    def test_unknown_or_missing_extension(self) -> None:
        with pytest.raises(FormatError, match="cannot infer"):
            format_from_path("captions.bin")
        with pytest.raises(FormatError, match="cannot infer"):
            format_from_path("captions")

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            (VTT, "vtt"),
            (ASS, "ass"),
            (SRT, "srt"),
            (TXT.replace("-->", "->"), "txt"),
            ('{"name":"x","cues":[]}', "json"),
            ('[{"start":0,"end":1,"text":"x"}]', "json"),
        ],
    )
    def test_detects_content(self, content: str, expected: str) -> None:
        assert detect_format(content) == expected

    def test_known_extension_wins_over_content(self) -> None:
        assert detect_format(SRT, filename="captions.vtt") == "vtt"

    def test_unknown_extension_falls_back_to_content(self) -> None:
        assert detect_format(VTT, filename="captions.bin") == "vtt"

    def test_detects_srt_with_three_digit_hours(self) -> None:
        content = "1\n100:00:01,000 --> 100:00:02,000\nLong programme\n"
        assert detect_format(content) == "srt"

    @pytest.mark.parametrize("content", ["ordinary prose", "{broken json", "[] nope"])
    def test_rejects_ambiguous_content(self, content: str) -> None:
        with pytest.raises(FormatError, match="could not detect"):
            detect_format(content)


class TestDecoding:
    def test_utf8_bom(self) -> None:
        text, encoding = decode_subtitle_bytes("\ufeffمرحبا".encode("utf-8"))
        assert text == "مرحبا"
        assert encoding == "utf-8-sig"

    def test_cp1252_fallback(self) -> None:
        text, encoding = decode_subtitle_bytes("café".encode("cp1252"))
        assert text == "café"
        assert encoding == "cp1252"

    def test_explicit_encoding(self) -> None:
        text, encoding = decode_subtitle_bytes("hello".encode("utf-16"), encoding="utf-16")
        assert text == "hello"
        assert encoding == "utf-16"

    def test_bad_explicit_encoding_is_domain_error(self) -> None:
        with pytest.raises(ParseError, match="cannot decode"):
            decode_subtitle_bytes(b"abc", encoding="not-an-encoding")

    def test_failed_auto_decode_lists_attempts(self) -> None:
        with pytest.raises(ParseError, match="cannot decode subtitle bytes"):
            decode_subtitle_bytes(b"\x81", fallback_encodings=())


class TestParsing:
    @pytest.mark.parametrize(
        ("content", "format_name", "count"),
        [
            (SRT, "srt", 2),
            (VTT, "vtt", 1),
            (ASS, "ass", 1),
            (TXT, "txt", 2),
            ('{"cues":[{"start":0,"end":1,"text":"Hi"}]}', "json", 1),
        ],
    )
    def test_parse_track_dispatch(self, content: str, format_name: str, count: int) -> None:
        parsed = parse_track(content, format_name, name="Named")
        assert parsed.name == "Named"
        assert len(parsed) == count

    def test_parse_track_uses_format_default_name(self) -> None:
        assert parse_track(SRT, "srt").name == "SRT Track"

    def test_load_uses_file_stem(self, tmp_path: Path) -> None:
        source = tmp_path / "episode.srt"
        source.write_text(SRT, encoding="utf-8")
        loaded = load_track(source)
        assert loaded.name == "episode"
        assert [cue.text for cue in loaded] == ["Hello, world!", "Second line"]

    def test_load_detects_extensionless_content(self, tmp_path: Path) -> None:
        source = tmp_path / "captions"
        source.write_text(VTT, encoding="utf-8")
        assert len(load_track(source)) == 1

    def test_load_format_override(self, tmp_path: Path) -> None:
        source = tmp_path / "captions.data"
        source.write_text(TXT, encoding="utf-8")
        assert len(load_track(source, format_name="txt", name="Override")) == 2

    def test_load_missing_and_directory_errors(self, tmp_path: Path) -> None:
        with pytest.raises(ParseError, match="file not found"):
            load_track(tmp_path / "missing.srt")
        with pytest.raises(ParseError, match="not a file"):
            load_track(tmp_path)


class TestSerialisation:
    @pytest.mark.parametrize("format_name", OUTPUT_FORMATS)
    def test_every_output_is_nonempty(self, track: Track, format_name: str) -> None:
        rendered = serialize_track(track, format_name)
        assert isinstance(rendered, str)
        assert rendered.strip()

    @pytest.mark.parametrize("format_name", INPUT_FORMATS)
    def test_round_trip_supported_inputs(self, track: Track, format_name: str) -> None:
        rendered = serialize_track(track, format_name)
        reparsed = parse_track(rendered, format_name, name="Round Trip")
        assert len(reparsed) == len(track)
        assert [cue.text for cue in reparsed] == [cue.text for cue in track]
        assert reparsed[0].start == pytest.approx(track[0].start, abs=0.01)
        assert reparsed[-1].end == pytest.approx(track[-1].end, abs=0.01)

    def test_json_is_valid_and_unicode_is_not_escaped(self, track: Track) -> None:
        track.cues[0] = track.cues[0].with_text("مرحبا")
        rendered = serialize_track(track, "json", json_indent=None)
        assert "مرحبا" in rendered
        assert json.loads(rendered)["cues"][0]["text"] == "مرحبا"

    @pytest.mark.parametrize("format_name", ["srt", "vtt"])
    def test_structured_text_preserves_internal_blank_lines(
        self, track: Track, format_name: str
    ) -> None:
        track.cues[0] = track.cues[0].with_text("First paragraph\n\nFinal paragraph")
        rendered = serialize_track(track, format_name)
        reparsed = parse_track(rendered, format_name)
        assert reparsed[0].text == track[0].text
        assert [cue.text for cue in reparsed] == [cue.text for cue in track]

    def test_csv_metadata_can_be_disabled(self, track: Track) -> None:
        rendered = serialize_track(track, "csv", include_csv_metadata=False)
        assert rendered.startswith("index,start,end,text,speaker,style")
        assert "# name:" not in rendered

    def test_ass_sanitises_fields_and_preserves_text(self) -> None:
        cue = Cue(1, 1, 2, r"{\i1}one{\i0}" + "\ntwo", speaker="A, B", style="Main,Alt")
        rendered = cues_to_ass([cue], title="A, title")
        assert "Title: A  title" in rendered
        assert "Style: Main Alt," in rendered
        assert "Main Alt,A  B" in rendered
        assert r"{\i1}one{\i0}\Ntwo" in rendered
        reparsed = parse_track(rendered, "ass")
        assert reparsed[0].text == r"{\i1}one{\i0}" + "\ntwo"


class TestWriting:
    def test_write_and_reload(self, track: Track, tmp_path: Path) -> None:
        destination = tmp_path / "out.srt"
        result = write_track(track, destination)
        assert result == destination
        assert load_track(destination).summary()["cue_count"] == 2
        assert not list(tmp_path.glob("*.tmp"))

    def test_existing_file_is_protected_by_default(self, track: Track, tmp_path: Path) -> None:
        destination = tmp_path / "out.vtt"
        destination.write_text("keep", encoding="utf-8")
        with pytest.raises(FormatError, match="already exists"):
            write_track(track, destination)
        assert destination.read_text(encoding="utf-8") == "keep"

    def test_overwrite_replaces_existing_file(self, track: Track, tmp_path: Path) -> None:
        destination = tmp_path / "out.vtt"
        destination.write_text("old", encoding="utf-8")
        write_track(track, destination, overwrite=True)
        assert destination.read_text(encoding="utf-8").startswith("WEBVTT")

    def test_no_overwrite_is_race_safe(
        self, track: Track, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import os

        destination = tmp_path / "raced.srt"
        real_link = os.link

        def create_competing_file_then_link(source: str, target: str | Path) -> None:
            Path(target).write_text("created by another process", encoding="utf-8")
            real_link(source, target)

        monkeypatch.setattr(os, "link", create_competing_file_then_link)
        with pytest.raises(FormatError, match="already exists"):
            write_track(track, destination)
        assert destination.read_text(encoding="utf-8") == "created by another process"
        assert not list(tmp_path.glob("*.tmp"))

    def test_explicit_format_supports_extensionless_output(
        self, track: Track, tmp_path: Path
    ) -> None:
        destination = tmp_path / "captions"
        write_track(track, destination, format_name="json")
        assert json.loads(destination.read_text(encoding="utf-8"))["name"] == "Demo"

    def test_missing_parent_is_rejected(self, track: Track, tmp_path: Path) -> None:
        with pytest.raises(FormatError, match="directory does not exist"):
            write_track(track, tmp_path / "missing" / "out.srt")

    def test_directory_destination_is_rejected(self, track: Track, tmp_path: Path) -> None:
        destination = tmp_path / "out.srt"
        destination.mkdir()
        with pytest.raises(FormatError, match="not a file"):
            write_track(track, destination, overwrite=True)


class TestSuggestedOutputPath:
    def test_changes_extension(self) -> None:
        assert suggested_output_path("movie.srt", "vtt") == Path("movie.vtt")

    def test_adds_sanitised_label(self) -> None:
        result = suggested_output_path("movie.srt", "json", suffix_label="shifted copy")
        assert result == Path("movie-shifted-copy.json")

    def test_empty_sanitised_label_is_ignored(self) -> None:
        assert suggested_output_path("movie.srt", "txt", suffix_label="***") == Path("movie.txt")
