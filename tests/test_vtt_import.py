"""Tests for vtt_import."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.errors import ParseError
from subcue.vtt_import import cues_to_vtt, parse_vtt_file, parse_vtt_text

VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.000
Hello, world!

2
00:00:05.500 --> 00:00:08.200
Second cue.
"""


class TestParseVttText:
    def test_basic(self):
        t = parse_vtt_text(VTT)
        assert len(t) == 2

    def test_missing_header_raises(self):
        with pytest.raises(ParseError):
            parse_vtt_text("1\n00:00:01.000 --> 00:00:02.000\nHi")

    def test_empty_raises(self):
        with pytest.raises(ParseError):
            parse_vtt_text("")

    def test_hourless_webvtt_timestamps(self):
        track = parse_vtt_text("WEBVTT\n\n00:01.000 --> 00:02.500\nHello\n")
        assert track[0].start == 1.0
        assert track[0].end == 2.5

    @pytest.mark.parametrize(
        "broken_block",
        [
            "3\n00:00:bad --> 00:00:12.000\nBroken cue",
            "broken-id\n00:00:bad --> 00:00:12.000\nBroken cue",
        ],
    )
    def test_malformed_cue_after_valid_cues_raises(self, broken_block: str):
        with pytest.raises(ParseError, match=r"block 3: .*timing line"):
            parse_vtt_text(f"{VTT}\n{broken_block}\n")

    def test_header_metadata_and_auxiliary_blocks_are_allowed(self):
        source = """WEBVTT - demonstration
Kind: captions
Language: en

NOTE an arrow --> inside a note is not a cue
This block is ignored.

STYLE
::cue { color: lime; }

REGION
id:main

X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:900000

named-cue
00:01.000 --> 00:02.500 align:start
Hello
"""
        track = parse_vtt_text(source)
        assert len(track) == 1
        assert track[0].text == "Hello"


class TestCuesToVtt:
    def test_roundtrip(self):
        t = parse_vtt_text(VTT)
        output = cues_to_vtt(t.cues)
        assert "WEBVTT" in output

    def test_blank_lines_inside_cue_text_survive_roundtrip(self):
        cues = [
            Cue(1, 1, 2, "First paragraph\n\n123"),
            Cue(2, 3, 4, "Next cue"),
        ]
        reparsed = parse_vtt_text(cues_to_vtt(cues))
        assert [cue.text for cue in reparsed] == [cue.text for cue in cues]


class TestParseVttFile:
    def test_file(self, tmp_path):
        p = tmp_path / "test.vtt"
        p.write_text(VTT)
        t = parse_vtt_file(str(p))
        assert len(t) == 2

    def test_missing(self):
        with pytest.raises(ParseError):
            parse_vtt_file("/nonexistent.vtt")
