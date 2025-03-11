"""Tests for txt_import."""

from __future__ import annotations

import pytest

from subcue.errors import ParseError
from subcue.txt_import import cues_to_txt, parse_txt_file, parse_txt_text

TXT = """00:00:01.000 --> 00:00:04.000 | Hello, world!
00:00:05.500 --> 00:00:08.200 | Second line.
"""


class TestParseTxtText:
    def test_basic(self):
        t = parse_txt_text(TXT)
        assert len(t) == 2

    def test_empty_raises(self):
        with pytest.raises(ParseError):
            parse_txt_text("")

    def test_bad_line_raises(self):
        with pytest.raises(ParseError):
            parse_txt_text("just-one-token")

    def test_comments_ignored(self):
        t = parse_txt_text("# comment\n" + TXT)
        assert len(t) == 2


class TestCuesToTxt:
    def test_roundtrip(self):
        t = parse_txt_text(TXT)
        output = cues_to_txt(t.cues)
        assert "Hello, world!" in output


class TestParseTxtFile:
    def test_file(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text(TXT)
        t = parse_txt_file(str(p))
        assert len(t) == 2

    def test_missing(self):
        with pytest.raises(ParseError):
            parse_txt_file("/nonexistent.txt")
