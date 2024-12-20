"""Tests for text_utils."""

from __future__ import annotations

from subcue.text_utils import (
    char_count,
    escape_html,
    extract_speaker,
    join_and,
    line_count,
    normalize_whitespace,
    slugify,
    strip_all_tags,
    strip_ass_tags,
    strip_bom,
    strip_html_tags,
    truncate,
    word_count,
    wrap_lines,
)


class TestStripTags:
    def test_html(self):
        assert strip_html_tags("<b>bold</b>") == "bold"

    def test_ass(self):
        assert strip_ass_tags("{\b1}bold{\b0}") == "bold"

    def test_all(self):
        assert strip_all_tags("<i>{\b1}text{\b0}</i>") == "text"

    def test_no_tags(self):
        assert strip_all_tags("plain text") == "plain text"


class TestNormalize:
    def test_whitespace(self):
        assert normalize_whitespace("  a   b  ") == "a b"

    def test_bom(self):
        assert strip_bom("\ufeffhello") == "hello"

    def test_no_bom(self):
        assert strip_bom("hello") == "hello"


class TestCounts:
    def test_word_count(self):
        assert word_count("hello world") == 2

    def test_char_count(self):
        assert char_count("hi") == 2

    def test_char_count_no_spaces(self):
        assert char_count("h i", exclude_spaces=True) == 2

    def test_line_count(self):
        assert line_count("a\nb\nc") == 3


class TestTruncate:
    def test_short(self):
        assert truncate("hi", 10) == "hi"

    def test_long(self):
        assert len(truncate("hello world foo", 10)) <= 10


class TestEscapeHtml:
    def test_basic(self):
        assert "&lt;" in escape_html("<b>")


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World!") == "hello-world"


class TestWrapLines:
    def test_basic(self):
        lines = wrap_lines("hello world this is a test", width=15)
        assert all(len(line) <= 16 for line in lines)


class TestExtractSpeaker:
    def test_with_speaker(self):
        sp, text = extract_speaker("JOHN: Hello there")
        assert sp == "JOHN" and text == "Hello there"

    def test_without(self):
        sp, text = extract_speaker("Just text")
        assert sp == "" and text == "Just text"


class TestJoinAnd:
    def test_three(self):
        assert join_and(["a", "b", "c"]) == "a, b and c"

    def test_one(self):
        assert join_and(["a"]) == "a"

    def test_empty(self):
        assert join_and([]) == ""
