"""Tests for ass_import."""

from __future__ import annotations

import pytest

from subcue.ass_import import parse_ass_file, parse_ass_styles, parse_ass_text
from subcue.errors import ParseError

ASS = """[Script Info]
Title: Test

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,Speaker1,0,0,0,,Hello from ASS!
Dialogue: 0,0:00:05.50,0:00:08.20,Default,,0,0,0,,Second line.
"""


class TestParseAssText:
    def test_basic(self):
        t = parse_ass_text(ASS)
        assert len(t) == 2

    def test_speaker(self):
        t = parse_ass_text(ASS)
        assert t[0].speaker == "Speaker1"

    def test_style(self):
        t = parse_ass_text(ASS)
        assert t[0].style == "Default"

    def test_empty_raises(self):
        with pytest.raises(ParseError):
            parse_ass_text("")

    def test_no_dialogue_raises(self):
        with pytest.raises(ParseError):
            parse_ass_text("[Script Info]\nTitle: Empty\n")

    def test_effect_and_commas_in_text_are_supported(self):
        source = """[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:02.00,Default,A,0,0,0,karaoke,Hello, world
"""
        cue = parse_ass_text(source)[0]
        assert cue.speaker == "A"
        assert cue.text == "Hello, world"

    def test_dynamic_event_format_order_is_respected(self):
        source = """[Events]
Format: Start, End, Name, Style, Text
Dialogue: 0:00:01.00,0:00:02.00,A,Alt,Hello
"""
        cue = parse_ass_text(source)[0]
        assert (cue.start, cue.end, cue.speaker, cue.style, cue.text) == (
            1.0,
            2.0,
            "A",
            "Alt",
            "Hello",
        )

    def test_inline_ass_formatting_is_preserved(self):
        source = """[Events]
Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,{\\i1}Hello{\\i0}
"""
        cue = parse_ass_text(source)[0]
        assert cue.text == r"{\i1}Hello{\i0}"
        assert cue.plain_text == "Hello"


class TestParseAssStyles:
    def test_basic(self):
        styles = parse_ass_styles(ASS)
        assert len(styles) >= 1
        assert styles[0].name == "Default"


class TestParseAssFile:
    def test_file(self, tmp_path):
        p = tmp_path / "test.ass"
        p.write_text(ASS)
        t = parse_ass_file(str(p))
        assert len(t) == 2

    def test_missing(self):
        with pytest.raises(ParseError):
            parse_ass_file("/nonexistent.ass")
