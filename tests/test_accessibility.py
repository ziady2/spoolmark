"""Tests for accessibility."""

from __future__ import annotations

from subcue.accessibility import (
    alt_text_for_chart,
    aria_label,
    contrast_check,
    focus_order,
    heading_hierarchy,
    screen_reader_table,
    simplify_text,
)


class TestAriaLabel:
    def test_basic(self):
        assert aria_label("button", "Play") == "button: Play"


class TestAltText:
    def test_with_title(self):
        t = alt_text_for_chart("bar", "CPS distribution", title="Analysis")
        assert "bar chart" in t and "Analysis" in t


class TestScreenReaderTable:
    def test_basic(self):
        t = screen_reader_table([{"a": 1}], title="T")
        assert "Table: T" in t

    def test_empty(self):
        assert "Empty" in screen_reader_table([])


class TestContrastCheck:
    def test_bw(self):
        r = contrast_check("#000000", "#ffffff")
        assert r["aaa_normal"] is True


class TestFocusOrder:
    def test_basic(self):
        els = [
            {"id": "b", "position": {"x": 100, "y": 200}},
            {"id": "a", "position": {"x": 50, "y": 100}},
        ]
        assert focus_order(els)[0]["id"] == "a"


class TestHeadingHierarchy:
    def test_valid(self):
        r = heading_hierarchy([(1, "A"), (2, "B")])
        assert all(h["valid"] for h in r)

    def test_skip(self):
        r = heading_hierarchy([(1, "A"), (3, "C")])
        assert r[1]["valid"] is False


class TestSimplifyText:
    def test_basic(self):
        t = simplify_text("\u250c\u2500\u2500\u2510")
        assert "+" in t and "-" in t
