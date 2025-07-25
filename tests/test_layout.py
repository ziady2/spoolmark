"""Tests for layout."""

from __future__ import annotations

from subcue.layout import (
    Grid,
    Section,
    horizontal_rule,
    page_header,
    truncate,
    two_column,
    wrap_lines,
    wrap_text,
)


class TestGrid:
    def test_exists(self):
        assert Grid is not None


class TestSection:
    def test_exists(self):
        assert Section is not None


class Test_horizontal_rule:
    def test_callable(self):
        assert callable(horizontal_rule)


class Test_page_header:
    def test_callable(self):
        assert callable(page_header)


class Test_truncate:
    def test_callable(self):
        assert callable(truncate)


class Test_two_column:
    def test_callable(self):
        assert callable(two_column)


class Test_wrap_lines:
    def test_callable(self):
        assert callable(wrap_lines)


class Test_wrap_text:
    def test_callable(self):
        assert callable(wrap_text)

    def test_returns_joined_text_not_internal_line_list(self):
        result = wrap_text("one two three four", width=9)
        assert result == "one two\nthree\nfour"
        assert isinstance(result, str)

    def test_applies_indent_to_each_line(self):
        assert wrap_text("one two three", width=8, indent="> ") == "> one\n> two\n> three"
