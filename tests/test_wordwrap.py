"""Behavioral tests for markup-aware subtitle wrapping."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from subcue.wordwrap import balance_score, check_line_lengths, rebalance_lines, wrap_subtitle


def _visible_text(text: str) -> str:
    without_html = re.sub(r"""<(?:(?:"[^"]*")|(?:'[^']*')|[^'">])*>""", "", text)
    return re.sub(r"\{[^}]*\}", "", without_html)


def _visible_words(text: str) -> list[str]:
    return _visible_text(text).split()


def _assert_html_lines_are_balanced(text: str) -> None:
    for line in text.splitlines():
        ET.fromstring(f"<root>{line}</root>")


class TestWrapSubtitle:
    def test_preserves_already_conforming_text_exactly(self):
        assert wrap_subtitle("Hello", max_width=42) == "Hello"

    def test_preserves_conforming_existing_newlines(self):
        assert wrap_subtitle("short\nlines", max_width=20, max_lines=2) == "short\nlines"

    def test_rewraps_when_existing_newlines_exceed_line_limit(self):
        assert wrap_subtitle("short\nlines", max_width=20, max_lines=1) == "short lines"

    def test_strictly_conforms_when_a_partition_exists(self):
        original = "one two three four five six"
        result = wrap_subtitle(original, max_width=13, max_lines=2)

        assert check_line_lengths(result, max_width=13, max_lines=2)["conformant"]
        assert _visible_words(result) == original.split()

    def test_impossible_capacity_uses_only_the_final_line_for_overflow(self):
        original = "one two three four"
        result = wrap_subtitle(original, max_width=5, max_lines=2)
        lines = result.splitlines()

        assert len(lines) == 2
        assert len(_visible_text(lines[0])) <= 5
        assert len(_visible_text(lines[-1])) > 5
        assert _visible_words(result) == original.split()

    def test_single_line_overflow_preserves_every_word(self):
        original = "one two three"
        result = wrap_subtitle(original, max_width=3, max_lines=1)

        assert result == original
        assert _visible_words(result) == original.split()

    def test_overlong_token_is_never_split_or_truncated(self):
        token = "extraordinary"
        result = wrap_subtitle(f"tiny {token} tail", max_width=5, max_lines=2)

        assert token in result.split()
        assert _visible_words(result) == ["tiny", token, "tail"]
        assert len(result.splitlines()) <= 2

    def test_html_spanning_generated_lines_is_closed_and_reopened(self):
        original = "<i>one two three four</i>"
        result = wrap_subtitle(original, max_width=10, max_lines=2)

        assert result == "<i>one two</i>\n<i>three four</i>"
        assert _visible_words(result) == ["one", "two", "three", "four"]
        _assert_html_lines_are_balanced(result)

    def test_nested_html_and_quoted_attribute_are_kept_atomic(self):
        original = '<font color="red" title="a > b"><i>one two</i> three four five</font>'
        result = wrap_subtitle(original, max_width=13, max_lines=2)

        assert _visible_words(result) == ["one", "two", "three", "four", "five"]
        assert all(len(_visible_text(line)) <= 13 for line in result.splitlines())
        assert 'title="a > b"' in result
        _assert_html_lines_are_balanced(result)

    def test_ass_override_blocks_are_never_split(self):
        original = r"{\i1}one two three four{\i0}"
        result = wrap_subtitle(original, max_width=10, max_lines=2)

        assert result.count(r"{\i1}") == 1
        assert result.count(r"{\i0}") == 1
        assert _visible_words(result) == ["one", "two", "three", "four"]
        assert all(part.count("{") == part.count("}") for part in result.split())

    def test_empty_and_whitespace_only_text_are_lossless(self):
        assert wrap_subtitle("") == ""
        assert wrap_subtitle("   ") == "   "

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("max_width", 0),
            ("max_width", -1),
            ("max_width", 1.5),
            ("max_width", True),
            ("max_lines", 0),
            ("max_lines", 1.5),
            ("max_lines", False),
        ],
    )
    def test_rejects_invalid_limits(self, name, value):
        with pytest.raises(ValueError):
            wrap_subtitle("some text", **{name: value})

    def test_rejects_non_string_text(self):
        with pytest.raises(TypeError, match="text must be a string"):
            wrap_subtitle(None)  # type: ignore[arg-type]


class TestCheckLineLengths:
    def test_reports_visible_metrics_and_ignores_markup_width(self):
        report = check_line_lengths("<i>12345</i>\n<b>12</b>", max_width=5, max_lines=2)

        assert report == {
            "conformant": True,
            "line_count": 2,
            "max_line_length": 5,
            "issues": [],
        }

    def test_reports_every_width_and_line_count_problem(self):
        report = check_line_lengths("1234\n12\n56789", max_width=3, max_lines=2)

        assert report["conformant"] is False
        assert report["line_count"] == 3
        assert report["max_line_length"] == 5
        assert report["issues"] == [
            "too many lines: 3 > 2",
            "line 1 too long: 4 > 3",
            "line 3 too long: 5 > 3",
        ]

    def test_empty_text_has_zero_lines(self):
        assert check_line_lengths("")["line_count"] == 0

    @pytest.mark.parametrize("kwargs", [{"max_width": 0}, {"max_lines": 0}])
    def test_validates_limits(self, kwargs):
        with pytest.raises(ValueError):
            check_line_lengths("text", **kwargs)


class TestBalanceScore:
    def test_equal_visible_lengths_are_perfect(self):
        assert balance_score("<i>1234</i>\n1234") == 1.0

    def test_single_line_is_perfect(self):
        assert balance_score("Hello") == 1.0

    def test_uneven_lines_score_between_zero_and_one(self):
        score = balance_score("123456\n12")
        assert 0.0 < score < 1.0

    def test_extreme_imbalance_is_clamped_to_zero(self):
        assert balance_score("abcdefghij\n\n\n") == 0.0

    def test_all_blank_lines_are_well_defined(self):
        assert balance_score("\n\n") == 1.0


class TestRebalanceLines:
    def test_flattens_and_balances_existing_lines(self):
        original = "This is\na test of rebalancing lines"
        result = rebalance_lines(original, max_width=20)

        assert _visible_words(result) == original.split()
        assert len(result.splitlines()) <= 2

    def test_does_not_split_html_attributes_on_spaces(self):
        original = '<font color="bright red">one two\nthree four</font>'
        result = rebalance_lines(original, max_width=10)

        assert 'color="bright red"' in result
        assert _visible_words(result) == ["one", "two", "three", "four"]
        _assert_html_lines_are_balanced(result)
