"""Tests for srt_import."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.errors import ParseError
from subcue.srt_import import cues_to_srt, parse_srt_file, parse_srt_text

SRT = """1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,500 --> 00:00:08,200
Second cue.
"""


class TestParseSrtText:
    def test_basic(self):
        t = parse_srt_text(SRT)
        assert len(t) == 2 and t[0].text == "Hello, world!"

    def test_timecodes(self):
        t = parse_srt_text(SRT)
        assert abs(t[0].start - 1.0) < 0.01
        assert abs(t[0].end - 4.0) < 0.01

    def test_empty_raises(self):
        with pytest.raises(ParseError):
            parse_srt_text("")

    def test_bom(self):
        t = parse_srt_text("\ufeff" + SRT)
        assert len(t) == 2

    def test_no_valid_cues_raises(self):
        with pytest.raises(ParseError):
            parse_srt_text("just some random text")

    @pytest.mark.parametrize(
        "broken_block",
        [
            "3\n00:00:bad --> 00:00:12,000\nBroken cue",
            "00:00:bad --> 00:00:12,000\nBroken cue",
        ],
    )
    def test_malformed_cue_after_valid_cues_raises(self, broken_block: str):
        with pytest.raises(ParseError, match=r"block 3: .*timing line"):
            parse_srt_text(f"{SRT}\n{broken_block}\n")


class TestCuesToSrt:
    def test_roundtrip(self):
        t = parse_srt_text(SRT)
        output = cues_to_srt(t.cues)
        assert "Hello, world!" in output

    def test_blank_lines_inside_cue_text_survive_roundtrip(self):
        cues = [
            Cue(1, 1, 2, "First paragraph\n\n123"),
            Cue(2, 3, 4, "Next cue"),
        ]
        reparsed = parse_srt_text(cues_to_srt(cues))
        assert [cue.text for cue in reparsed] == [cue.text for cue in cues]

    def test_hundred_hour_timestamp_is_parseable(self):
        cue = Cue(1, 100 * 3600 + 1.234, 100 * 3600 + 2.5, "Long programme")
        rendered = cues_to_srt([cue])
        assert "100:00:01,234 --> 100:00:02,500" in rendered
        reparsed = parse_srt_text(rendered)
        assert reparsed[0].start == pytest.approx(cue.start, abs=0.001)
        assert reparsed[0].end == pytest.approx(cue.end, abs=0.001)


class TestParseSrtFile:
    def test_file(self, tmp_path):
        p = tmp_path / "test.srt"
        p.write_text(SRT)
        t = parse_srt_file(str(p))
        assert len(t) == 2

    def test_missing(self):
        with pytest.raises(ParseError):
            parse_srt_file("/nonexistent.srt")
